# Driftfall: observable rules

This document describes the game's observable behaviour. No internal design is prescribed.
Coordinates are integers, x increases right, y increases down.

## 1. Base game and JSON-lines protocol

Read UTF-8 JSON lines until EOF. Answer every line with exactly one JSON object and newline,
including blank or invalid lines, and flush the answer. No other stdout output is permitted.
A final line without a newline is also answered. JSON objects use the last value of a duplicate
key. Non-JSON extensions (NaN, Infinity, trailing data) are invalid. Successful commands other
than state return exactly `{"ok":true}`. State returns exactly `{"ok":true,"state":SNAPSHOT}`.
Errors return exactly `{"ok":false,"error":CODE}`. Object member order is irrelevant.
Every refusal leaves all state, including hidden generator and gravity progress, unchanged.

Commands and exact allowed members:
- `{"cmd":"new","seed":42}`: seed is an integer 0..4294967295. Reset everything and spawn.
- `{"cmd":"input","key":"left"}`: keys are left, right, rotate, soft, hard.
- `{"cmd":"tick","ms":16}`: ms is an integer 0..1000000.
- `{"cmd":"state"}`: inspect without changing anything.

Unknown members are refused. JSON numbers written as fractions or exponents are not integers
for this protocol, even if mathematically integral. Booleans are not numbers. Validation order:
invalid JSON -> bad_json; non-object, missing/non-string cmd -> bad_request; unknown command
-> unknown_command; wrong members, missing fields, wrong types/ranges or unknown input key ->
bad_request; then phase restrictions below. The error codes are
`bad_json`, `bad_request`, `unknown_command`, `not_started`, `finished`.
Before new, phase is idle; input/tick refuse not_started. In over, they refuse finished.
New and state always work (subject to field validation), even after game over.

The board has 10 columns and 18 rows. Snapshot board is 18 top-to-bottom strings of length 10:
`.` means empty and `#` means locked. It never includes active cells. The snapshot has
exactly phase, board, active, score, lines, level. Initially: phase idle, empty board, active null,
score=0, lines=0, level=1. During play phase is playing. Active is an object with exactly kind
(a name below) and cells (absolute `[x,y]` pairs sorted by y, then x). Over has active null.

Five pieces have these initial local occupied cells (not existing tetrominoes):
- sprig: (0,0), (0,1), (1,1) [3 cells]
- prong: (0,0), (1,0), (2,0), (1,1), (1,2) [5 cells]
- ramp: (0,0), (0,1), (1,1), (1,2), (2,2) [5 cells]
- arch: (0,0), (2,0), (0,1), (1,1), (2,1) [5 cells]
- reed: (0,0), (0,1), (0,2), (0,3), (1,3) [5 cells]

Each spawn resets orientation and places the top-left of the local bounding box at x=4,y=0.
If any spawn cell is out of bounds or on a locked cell, enter over and set active null.
The generator starts with seed, replacing 0 with 2463534242. Drawing advances xorshift32:
`x ^= (x << 13); x ^= (x >> 17); x ^= (x << 5)`; after EACH operation mask to 32 bits.
A draw selects index x modulo 5 from [sprig, prong, ramp, arch, reed]. A fresh game consumes
one draw for its active piece. Only spawning a new drawn piece consumes another draw.

Left/right translates one column. Clockwise rotation maps each local (x,y) to (h-1-y,x),
where h is current local bounding-box height, then subtracts the minimum x and y from all
cells; it keeps the bounding-box origin fixed. A blocked move or rotation succeeds but changes
nothing; there are no kicks. Soft moves down one row for +1 score if possible; if blocked it
locks immediately for no drop points. Hard moves down as far as possible (+2 per row) then
locks, including at zero distance. Translation/rotation never locks on their own.

A normal lock deposits active cells as # and awards 7 points. Simultaneously remove ALL full
rows and prepend equally many empty rows. For n rows, award `80*n*n*old_level`. Then increase
lines by n and set level to `1 + floor(lines/4)`. Spawn the next piece. No score is negative.
Gravity interval in milliseconds is `max(90, 600-45*(level-1))`. An accumulator starts at zero.
Tick adds ms, then while playing and accumulator >= the CURRENT interval: subtract that
interval, attempt one downward move without drop points, and lock if blocked. EVERY lock
resets the accumulator to zero, discarding any remaining credit from that tick. Inputs never
advance time. New resets the accumulator. Only ticks advance time; there is no wall clock.

## 2. Pause

Add `{"cmd":"pause"}` and `{"cmd":"resume"}`, with no other members. Pause playing -> paused;
resume paused -> playing. Repeating pause while paused or resume while playing succeeds without
change. Input and tick while paused refuse `paused`. Pause/resume before new refuse not_started;
in over refuse finished. State and new remain usable. Pause preserves gravity
credit; refused ticks contribute nothing.

## 3. Hold and preview

Add input key hold. Add snapshot members held (kind or null), preview (next three kinds in order),
and hold_available (boolean). Initially idle: held null, preview [], hold_available false.
New fills the three-item preview immediately after drawing active. When taking from preview,
remove its first item and replenish by one draw. These draws do not alter the active sequence
from section 1. Hold is available at every normal spawn after a lock and initially after new.
Hold stores the current kind; with no held kind it spawns from preview, otherwise it swaps the
held and current kinds without drawing. The incoming piece always uses initial orientation and
spawn position. Reset gravity credit on hold. Even an unsuccessful spawn consumes the hold and
enters over. Hold once makes hold_available false until the next lock; a second hold refuses
`hold_used`. Phase errors take precedence over hold_used. Pause and resume leave hold_available unchanged.
On over, hold_available is false.

## 4. Pulse

Add the kind pulse: initial local cells (0,0), (0,1), (0,2). For each draw, after advancing the
same generator, select pulse if x modulo 16 is 15; otherwise retain x modulo 5 as above.
Pulse's clockwise rotation leaves its cells unchanged. On locking pulse, it deposits no cells:
erase existing locked cells in the clipped 3x3 square centered on its bottom cell. Award
`11 + 3*erased_cell_count` lock points instead of 7; drop points still apply. Then perform the
ordinary full-row removal, level update, and subsequent spawn. All other piece facts stay the same.

## 5. Modes and time

New optionally accepts mode, exactly endless or rush; omission means endless. Add snapshot
members mode and elapsed_ms. Idle uses endless and 0. New resets elapsed_ms to 0. A playing
tick adds its ENTIRE ms to elapsed_ms before gravity, even if this tick finishes the game.
Paused, idle, finished, refused, and input commands add no time. Endless has the prior rules.
Rush wins immediately when a lock brings total lines to at least 4. Set phase won, active null,
hold_available false, gravity credit zero; do not draw/spawn a subsequent piece. Winning takes
precedence over a blocked next spawn. Won has the same command refusals as over.

## 6. Replay import

Add `{"cmd":"replay","document":DOCUMENT}` with no other members. DOCUMENT has exactly seed,
mode, events, end_ms. Seed and mode use new's ranges; mode is required. Events is an array of
0..4096 objects, each with exactly at_ms and key. Times and end_ms are integers 0..1000000;
event times are nondecreasing (equal times retain array order) and no event exceeds end_ms.
Keys are left, right, rotate, soft, hard, hold, pause, resume. All structural, type, range, key,
or ordering errors inside document refuse `bad_replay` without changing ANY state. A missing
document or extra top-level member instead gives bad_request.

A valid replay replaces the current game with a fresh new(seed,mode). Starting at t=0, before
each event feed tick(event.at_ms - previous_time), then its input (pause/resume mean their
commands); after the last event feed tick(end_ms - previous_time). This includes zero-duration
ticks. Ignore gameplay refusals (paused, hold_used, finished) during this playback exactly as
live commands would leave state unchanged. Valid replay succeeds from any current phase and
returns only ok:true. Empty events still executes the final tick. Validation of the whole
document happens before any playback. Resume never accounts for skipped paused time.

The complete closed error-code list is bad_json, bad_request, unknown_command, not_started,
finished, paused, hold_used, bad_replay. Snapshot fields are exactly the union introduced so far;
no accumulator, random state, internal orientation, or implementation details are exposed.
