# Ashline skirmish instrument

Run the complete audit:

```sh
python3 benchmark/games/tasks/skirmish/selftest.py
```

The audit builds each project in temporary directories inside this task, runs its
documented CI, checks the cumulative hidden tests, rejects preceding steps and empty
fixtures, and checks that every deliberately missed rule passes earlier tests but
fails its own step. Success is 50 `ok` lines followed by `instrument valid`.
Builds, Go caches and temporary files are removed before that final line.

`GAME_BIN` names the executable for standalone hidden tests. Run them with pytest
and `-p no:cacheprovider`. Tests communicate only through JSON lines.
Goldens are committed JSON literals; neither reference language supplies expected replies.
Each step's seeded fuzz test runs 2,000 mixed commands plus query/outcome probes and
future-play comparisons against a twin that never receives refused commands.
Earlier files sample unchanged cases for rules replaced by subsequent steps.

The `tools/` scripts reproduce the cumulative reference projects, literal scenarios
and small per-step test entry files. Source templates remove future branches before
writing each project. Generation uses only Python's standard library, cargo fmt and
gofmt; it installs nothing. Keep generation tools, hidden tests and references outside
agent-visible fixtures. The harness the brief describes is `benchmark/games/games.py`.
