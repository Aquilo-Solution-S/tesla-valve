<!-- The brief as given to the model that built this game, unchanged. Its paths are those of the
machine it was built on; the game now lives in this directory. -->

# Brief: game 2 of the game-evolution benchmark ("two-player skirmish with fog of war")

You build ONE task, `/tmp/tv-bench/games/tasks/skirmish/`, as an instrument. Write ONLY inside that
directory. Install nothing. Use `/tmp/tv-ex-venv/bin/python` (pytest 9) for the hidden tests, the
user's `cargo` (Rust may use only `serde` and `serde_json`, already in the cargo cache: the fixture
must build with `cargo build --offline`; set `RUSTC_WRAPPER=` for every cargo call) and `go`
(standard library only).

Game 1 of this benchmark is `/tmp/tv-bench/games/tasks/driftfall/`. Read its `selftest.py`,
`hidden/conftest.py` and `hidden/checks.py` first and reuse what fits (the JSON-lines driver, the
twin-game refusal check, the cumulative selftest); do not copy its game.

## How the instrument is used (do not build this part)

An agent builds the game into an empty language fixture from `steps/f1.md` and the spec; fresh agent
sessions then implement `steps/f2.md` ... `steps/f6.md` one by one on top of what the previous step
left. Before step k the harness writes the project's `spec.md` as the intro plus sections 1..k ONLY,
so the agent never sees a later step. After every step the language's CI runs (one fix round), then
the harness builds the binary and runs the hidden tests of ALL steps so far, so regressions count.
The arms differ only in the agents' global instructions; the tests must never favour one design.
Agents never see `hidden/`, `ref/` or this brief.

## Lessons from game 1 (binding)

- `spec.md` is an intro plus sections `## 1. ...` to `## 6. ...`, one per step, in order. The intro
  and every section must read as complete on their own: no "completed game", no "initially", no
  "later", no mention of anything a later section adds. A section may refer to earlier sections.
- Close every ambiguity a careful reader could resolve two ways. For every snapshot/view field,
  the section that introduces it states its value in every phase that exists at that point, and
  every later section that adds a phase or command states what it does to existing fields.
- Strong models reached 100% on game 1, so this game must also test what the code CARRIES when an
  existing rule CHANGES, not only when features are added (see f2 and f5).

## The game (invent names and numbers; nothing from an existing game)

Two players command small squads on a fixed map of about 9 x 9 cells defined literally in the spec
(at least three terrain kinds, one of them impassable for most units). Three unit kinds with hit
points, attack, range and movement. Fully deterministic: no random numbers at all.

- Turns are simultaneous: each player submits at most one order per own unit (move to a cell, or
  attack a unit, or hold), may replace an order before ending the turn, then ends the turn. When
  both players have ended the turn it resolves in an exact order the spec defines: all moves at
  once (two units entering the same cell, or two units swapping cells, both stay where they were),
  then all attacks at once (damage applied together, units at 0 hp removed after all attacks).
  The game ends when a side has no units (won by the other, or a draw if both are emptied at once).
- Two QUERIES share rules with the turn resolution from f1 on, and the spec says they must always
  agree with it: `reachable` (the exact set of cells a unit's move order would accept) and
  `forecast` (the exact damage an attack order would deal if it resolved now). Hidden tests check
  query against outcome.

## The protocol (pinned in spec.md; the only design spec.md prescribes)

As in game 1: JSON lines in, exactly one JSON line out per input line, in order, exit at EOF;
success `{"ok": true, ...}`, refusal `{"ok": false, "error": "<code>"}` from a closed list in the
spec; a refused or malformed line changes no state and never ends the process. Commands such as
`new`, `order`, `end_turn`, `state`, `reachable`, `forecast`. Snapshots are fully specified (turn
number, phase, units with id, owner, kind, position, hp, pending-order status). `spec.md` says
nothing about internal design: no types, modules or patterns, only behaviour.

## The six steps (business words only; each 3-10 lines, naming no code)

- f1: the base game above, with `reachable` and `forecast`.
- f2: RULE CHANGE: terrain now has movement costs (one terrain costs more, one stays impassable,
  one unit kind may cross it). Movement range becomes a path cost budget. `reachable`, order
  validation and resolution must all follow the new rule; the step text names only the rule.
- f3: fog of war. A new per-player `view` command shows only what that player's units can see
  (a sight rule per kind). The full `state` stays as an observer command. RULE CHANGE hidden in
  the facts: a player's order must be accepted or refused using only what that player can see, so
  an order onto a cell held by an unseen enemy is accepted (resolution settles it), and no reply
  to a player-scoped command may reveal an unseen unit (error codes included). The step text states
  the visibility facts and the no-leak rule, not the consumers.
- f4: a fourth unit kind with its own facts (for example it repairs an adjacent ally instead of
  attacking, with its own sight and movement). At least two consumers that must change are NOT
  named by the step text but follow from the facts (for example `forecast`, the visibility rule,
  the resolution order, or the end condition for a side left with only this kind) - the trap.
- f5: RULE CHANGE to combat: damage now depends on terrain or position (for example defence on one
  terrain, or a counter-strike rule), replacing the f1 damage rule. `forecast` must still agree
  with resolution; the step text names only the new rule.
- f6: export and import: `export` returns the whole game as a document; `import` takes one and
  replaces the game. Any invalid document (bad structure, unknown kind, unit off the map or on a
  cell its kind cannot stand on, two units on one cell, hp out of range, orders for missing units,
  inconsistent turn state) is refused with a named code and leaves the current game exactly as it
  was; a valid export/import round trip continues identically to the original.

## Layout (all required, as in game 1)

- `spec.md` (intro + sections 1..6), `steps/f1.md` to `steps/f6.md`.
- `fixture/rust/` and `fixture/go/`: empty projects that build, each with a README stating the CI
  commands (Rust `cargo fmt --check`, `cargo clippy --offline -- -D warnings`, `cargo test --offline`;
  Go `test -z "$(gofmt -l .)"`, `go vet ./...`, `go test ./...`) and how the binary is built (Rust
  `cargo build --release --offline`; Go `go build -o game .` from the project root).
- `hidden/conftest.py`, `hidden/test_f1.py` to `test_f6.py`: scripted scenarios with exact expected
  replies and snapshots as committed literals; a seeded fuzz test per file (at least 2,000 commands,
  valid and invalid mixed) with invariants after every reply (every line answered, refused lines
  change nothing including hidden state via a twin game, units in bounds and on legal terrain, no
  two units on a cell, hp in range, `reachable` and `forecast` agree with what an order then does,
  from f3 no player-scoped reply reveals an unseen unit); the refusal tests for that step's inputs.
  Earlier steps' assertions must keep passing on correct later implementations (compare only the
  fields a step specified). Every assertion must follow from the spec sections and step texts so far.
- `ref/rust/f1` ... `ref/rust/f6` and `ref/go/f1` ... `ref/go/f6`: complete projects, each step
  building on the previous one, written as a careful engineer would; every one passes its CI.
- `ref_missed/rust/f2` (rule changed in validation but not in `reachable`, or the reverse),
  `ref_missed/rust/f3` (one leak of an unseen unit), `ref_missed/rust/f5` (`forecast` keeps the old
  rule) and `ref_missed/rust/f6` (one validation gap): each is the previous ref plus a plausible step
  with exactly that miss.
- `selftest.py`: as in game 1: every `ref/<lang>/fK` passes CI and hidden f1..fK; `test_fK` FAILS on
  `ref/<lang>/f(K-1)` for K >= 2; each empty fixture fails test_f1; each `ref_missed` passes the earlier
  test files and fails its targeted one. One `ok`/`XX` line per check, `instrument valid` last.

## Do not stop until

`/tmp/tv-ex-venv/bin/python /tmp/tv-bench/games/tasks/skirmish/selftest.py` prints only `ok` lines
and `instrument valid`. Leave no `target/` or built binaries inside the task directory.

## Report (max 250 words)

The selftest summary, ref line counts per language and step, each ref_missed trap in one sentence,
the fuzz invariants, and anything in the spec you consider ambiguous.
