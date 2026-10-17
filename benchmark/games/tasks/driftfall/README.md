# Driftfall instrument

The game contract is in `spec.md`; the six incremental business requests are in `steps/`.
Fixtures are empty, buildable projects. Each reference directory is a standalone cumulative
implementation at the named step. The two missed Rust references deliberately contain one
omission apiece. Hidden tests communicate exclusively with `GAME_BIN` over JSON lines.

Run the complete audit:

```sh
python3 benchmark/games/tasks/driftfall/selftest.py
```

A successful audit prints 44 `ok` lines followed by `instrument valid`. It checks language CI,
all cumulative hidden tests, feature dependence on each step, empty fixtures, and both missed
references. Every hidden test file includes its own reproducible 2,000-command fuzz run.
The committed scenario files contain literal expected snapshots; tests do not execute an oracle
or import either reference. Earlier tests compare their specified snapshot fields and allow
later additions. Their exact piece streams avoid the newly designated pulse outcomes.

The audit builds in a temporary directory inside this task and removes it on exit. Each Rust
project has its own target directory so builds with the same binary name cannot reuse another
step's executable. It disables the environment's optional compiler wrapper, which cannot run
in the sandbox. No installation, network, or extra language packages are needed.

`build_instrument.py` is the source authoring tool. It materializes and formats standalone
sources, excluding features not yet introduced at each step. `author_goldens.py` authors exact
scenarios using the independent rule model in `hidden/model.py`; committed move sequences
include a reachable simultaneous three-row clear. Neither authoring tool runs during testing.
