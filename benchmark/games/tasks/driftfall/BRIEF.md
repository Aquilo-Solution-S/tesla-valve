<!-- The brief as given to the model that built this game, unchanged. Its paths are those of the
machine it was built on; the game now lives in this directory. -->

# Brief: game 1 of the game-evolution benchmark ("falling blocks with its own pieces")

You build ONE task, `/tmp/tv-bench/games/tasks/driftfall/`, as an instrument. Write ONLY inside that
directory. Install nothing. Use `/tmp/tv-ex-venv/bin/python` (pytest 9) for the hidden tests, the
user's `cargo` (Rust may use only `serde` and `serde_json`, already in the cargo cache: the fixture
must build with `cargo build --offline`) and `go` (standard library only).

## How the instrument is used (do not build this part)

An agent builds the game from `spec.md` + `steps/f1.md` into an empty language fixture, then fresh
agent sessions implement `steps/f2.md` ... `steps/f6.md` one by one on top of what the previous step
left. After every step the language's CI runs (with one fix round), then the harness builds the
binary and runs the hidden tests of ALL steps so far, so regressions count. The arms differ only in
the agents' global instructions; the tests must never favour one design. Agents never see `hidden/`,
`ref/` or this brief.

## The game (invent the names and numbers; nothing from an existing game)

A falling-block puzzle on a grid of your choice (about 10 x 20) with its OWN set of five pieces
(polyominoes of 3 to 5 cells, named by you, not tetrominoes), driven headless:

- spawn, move left/right, rotate clockwise (rotation fails and changes nothing if blocked: no kicks),
  soft drop, hard drop, gravity by ticks, lock on landing, clear full rows, score, level, game over
  when a new piece cannot spawn.
- Deterministic across languages: `spec.md` defines the random generator exactly (for example
  xorshift32 with given shifts, seeded by the `new` command) and exactly how a piece kind is drawn
  from it; time advances only through `tick` commands with a millisecond argument, and the spec
  defines gravity as an exact accumulator rule. No wall clock anywhere.

## The protocol (pinned in spec.md; the only design spec.md prescribes)

The binary reads JSON lines on stdin and writes exactly one JSON line on stdout per input line, in
order, then exits at EOF. Commands such as `{"cmd":"new","seed":42}`, `{"cmd":"input","key":"left"}`,
`{"cmd":"tick","ms":16}`, `{"cmd":"state"}`. A success reply carries `"ok": true` (and the snapshot for
`state`); a refusal is `{"ok": false, "error": "<code>"}` with a closed list of codes in the spec.
A refused or malformed line (bad JSON, unknown command, missing or out-of-range field, wrong type)
changes no state and never ends the process. The snapshot is fully specified: phase, board rows as
strings, active piece kind and cells, score, lines, level, and the fields later steps add.
`spec.md` says nothing about internal design: no types, modules or patterns, only behaviour.

## The six steps (business words only; each 3-10 lines, naming no code)

- f1: the base game above.
- f2: pause and resume; while paused, ticks and moves are refused with a named code and change
  nothing; a finished game refuses both.
- f3: hold one piece (at most one swap per piece until it locks) and a preview of the next three
  pieces, both in the snapshot.
- f4: a sixth piece kind with its own behaviour on locking (for example it clears a small area
  instead of staying), its own score rule, and its own rotation rule. The step text states only the
  piece's facts. At least two consumers that must change are NOT named by the step text but follow
  from the facts (for example hold, preview, spawn weights or the snapshot) - the trap.
- f5: a second game mode chosen at `new` (for example "clear N rows as fast as possible"), with its
  own end condition and a won phase; elapsed time counts only ticked milliseconds while playing.
- f6: replay import: a command carries a replay document (seed, mode and a list of timed inputs);
  a valid one replays to the same final state as feeding the commands live; any invalid one (bad
  structure, unknown key, out-of-order times, negative times) is refused with a named code and
  leaves the current game exactly as it was.

## Layout (all required)

- `spec.md` (protocol, rules, generator, gravity rule, error codes, snapshot schema), `steps/f1.md` to
  `steps/f6.md`.
- `fixture/rust/` and `fixture/go/`: empty projects that build (a `main` that does nothing), each with
  a README stating the CI commands: Rust `cargo fmt --check`, `cargo clippy --offline -- -D warnings`,
  `cargo test --offline`; Go `test -z "$(gofmt -l .)"`, `go vet ./...`, `go test ./...`.
- `hidden/conftest.py`: a driver that starts `$GAME_BIN`, sends lines and reads replies, with a
  per-reply timeout; `hidden/test_f1.py` to `test_f6.py`. Each file: scripted scenarios with exact
  expected snapshots, a seeded fuzz test (at least 2,000 random commands, valid and invalid mixed)
  checking invariants after every reply (every line answered, refused lines change nothing, cells in
  bounds, no active cell on a locked cell, score never decreases, process alive), and the refusal
  tests for that step's new inputs. Behaviour only; every assertion must follow from spec.md and
  the step texts so far.
- `ref/rust/f1` ... `ref/rust/f6` and `ref/go/f1` ... `ref/go/f6`: complete projects, each step
  building on the previous one, written as a careful engineer would; every one passes its language's
  CI.
- `ref_missed/rust/f4`: `ref/rust/f3` plus a plausible f4 that adds the new piece but misses one
  unnamed consumer; likewise `ref_missed/rust/f6` with one plausible validation gap.
- `selftest.py`: builds a project, runs hidden tests and CI, and checks, for both languages:
  every `ref/<lang>/fK` passes CI and hidden tests f1..fK; `test_fK` FAILS on `ref/<lang>/f(K-1)` for
  K >= 2 (each step's tests need that step); the empty fixture fails test_f1; each `ref_missed`
  fails the targeted test file and passes the earlier ones. It prints one `ok`/`XX` line per check
  and `instrument valid` last.

## Do not stop until

`/tmp/tv-ex-venv/bin/python /tmp/tv-bench/games/tasks/driftfall/selftest.py` prints only `ok` lines
and `instrument valid`. Leave no `target/` or built binaries inside the task directory.

## Report (max 250 words)

The selftest output summary, fixture/ref line counts per language and step, the f4 and f6 traps in
one sentence each, the fuzz invariants, and anything in the spec you consider ambiguous.
