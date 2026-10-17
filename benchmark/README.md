# The benchmark

This is the game-evolution benchmark behind [RESULTS.md](../RESULTS.md): AI
agents grow a small game over six steps, with Tesla Valve and without, and a
blind judge from another vendor compares the final code. Everything needed to
run it again is here, and so are the runs the results cite.

## What is here

| Path | What it is |
| --- | --- |
| `games/games.py` | Runs the cells and reports the hidden tests. |
| `games/agents.py` | The authors, sandboxed, and the judges, which only read. |
| `games/pairwise.py` | The blind pairwise judgement of two arms' final code. |
| `games/tally.py` | Counts the verdicts of one or more runs. |
| `games/cost.py` | Compares an arm's time, tokens, dollars and lines with baseline. |
| `games/refactor.py` | Refactors the projects that grew without rules, once per arm, and checks that they still behave as before. |
| `games/refactor-plan.md` | The plan of the refactoring experiment, written before it ran. |
| `games/tasks/<game>/` | One game: `spec.md`, the six step prompts in `steps/`, empty fixtures for Rust and Go, hidden tests, reference solutions, and `selftest.py`. |
| `games/results/<run>/` | The published runs: one record per cell, the verdicts in `judged/`, and the code in `code.tar`. |
| `games/variants/v7a.patch` | The rules as measured: it undoes every line changed since, the one narrowed after the refactoring experiment and the few changed after a week of use. |
| `games/variants/r8a.patch` | The candidate rules that were tried and dropped, on top of the measured ones. |

A cell is one game, one language, one arm, one model and one run. Each of its
six steps is a fresh agent session. Then the project's CI runs, with one fix
round in the same session if it is red. Then the hidden tests of every step so
far run against the built program. Before step *k*, the agent sees `spec.md`
only up to section *k*.

## What you need

- Python 3.10 or later, with pytest.
- Rust with rustfmt and clippy, and Go.
- The `codex` CLI, signed in, for `gpt-*` models. The `claude` CLI, signed in,
  for Claude models. The published runs used codex-cli 0.162.0 and Claude Code
  2.1.296.
- macOS or Linux: both CLIs sandbox the authors. An author writes only the
  project and the toolchains' caches, and reaches no network. It can still
  read the rest of the machine, the hidden tests included. In the published
  Claude run, none of the 2,208 tool calls touched them. The Codex authors'
  session logs were not kept then. A run now keeps them in its `logs/`.

The builds run offline. Fetch the Rust dependencies once:

```sh
(cd benchmark/games/tasks/driftfall/fixture/rust && cargo fetch)
(cd benchmark/games/tasks/skirmish/fixture/rust && cargo fetch)
```

## Run it

From the repository root. First check that a game's instrument holds. The
reference solutions pass every step, and each deliberately broken one fails
its own step:

```sh
python3 benchmark/games/tasks/driftfall/selftest.py      # 44 ok, then "instrument valid"
python3 benchmark/games/tasks/skirmish/selftest.py       # 50 ok, then "instrument valid"
```

Then run cells, judge them, and count:

```sh
python3 benchmark/games/games.py --games driftfall,skirmish --langs rust,go \
    --arms baseline,tesla-valve --models gpt-6-luna --runs 3
python3 benchmark/games/pairwise.py benchmark/games/runs/<run> \
    --arms baseline,tesla-valve --judge claude-sonnet-5-5
python3 benchmark/games/tally.py benchmark/games/runs/<run>
```

Runs land in `benchmark/games/runs/`, which git ignores. `games.py --report
<run>` prints the hidden-test table again.

**Arms.** `baseline` runs without rules. `tesla-valve` runs with the rules of
this repository at every step. A Codex author gets its `AGENTS.md` as global
instructions. A Claude author loads a copy of the plugin with `--plugin-dir`,
as an installed plugin is a copy. Claude Code refuses to write inside a loaded
plugin's directory, and the cells live inside this one. Any other plugin
directory with an `AGENTS.md` is an arm too. The suffix `@first` gives the
rules to step 1 only. An arm directory's name labels its records, so these two
worktrees run the rules as measured, and the dropped candidate on top of them,
under the names the records use:

```sh
git worktree add --detach /tmp/tv-v7a
git -C /tmp/tv-v7a apply "$PWD/benchmark/games/variants/v7a.patch"
git worktree add --detach /tmp/tv-r8a
git -C /tmp/tv-r8a apply "$PWD/benchmark/games/variants/v7a.patch"
git -C /tmp/tv-r8a apply "$PWD/benchmark/games/variants/r8a.patch"
python3 benchmark/games/games.py --arms /tmp/tv-v7a,/tmp/tv-r8a --models gpt-6-luna
```

**The judge** must come from another vendor than the authors. `pairwise.py`
refuses otherwise, unless you pass `--same-vendor` for a cross-check. Its
default instructions, `neutral`, do not use Tesla Valve's vocabulary. `--rubric
v1` names the criteria directly.

## The published runs

| Run | Game | Author | Arms | Runs per language |
| --- | --- | --- | --- | --: |
| `20261010-120039` | driftfall | `gpt-6-luna` | baseline, tv-v7a, tv-v7a@first | 1 |
| `20261010-120859` | driftfall | `gpt-6.1-sol` | baseline, tv-v7a, tv-v7a@first | 1 |
| `20261010-120905` | driftfall | `gpt-6-luna` | baseline, tv-v7a, tv-v7a@first | 3 |
| `20261010-122156` | driftfall | `gpt-6.1-sol` | baseline, tv-v7a, tv-v7a@first | 2 |
| `20261010-131542` | skirmish | `gpt-6-luna` | baseline, tv-v7a, tv-r8a | 3 |
| `20261010-131545` | skirmish | `gpt-6.1-sol` | baseline, tv-v7a, tv-r8a | 2 |
| `20261010-142859` | both | `claude-haiku-5-5` | baseline, tv-v7a | 2 |

The records use the names the arms had while we tuned the rules:

- `tv-v7a` is the rules as measured: this repository's with
  `variants/v7a.patch` applied.
- `tv-v7a@first` is the same rules for step 1 only.
- `tv-r8a` is `tv-v7a` with `variants/r8a.patch` applied on top.

A cell directory spells `@first` as `+first`.

To count every verdict behind RESULTS.md:

```sh
python3 benchmark/games/tally.py benchmark/games/results/*
```

And the cost table:

```sh
python3 benchmark/games/cost.py benchmark/games/results/* --arm tv-v7a
```

Each verdict file is named after the two arms, the judge and the instructions.
The main table of RESULTS.md is the `neutral` verdicts from a judge of the
other vendor. The `gpt-6.1-sol` verdicts on `gpt-6.1-sol` code are the
same-vendor cross-check.

`code.tar` holds one git bundle per cell. Each bundle has one commit for the
fixture, then for each step one for the spec section and one for the code the
agent left:

```sh
mkdir code && tar -xf benchmark/games/results/20261010-142859/code.tar -C code
git clone code/skirmish__rust__tv-v7a__claude-haiku-5-5__0.bundle
```

## Refactoring

`refactor.py` takes the projects that published runs grew without rules, as
they stood after step 6. The model that grew each one refactors it once per
arm, in a fresh session with CI and one fix round:

- `baseline` runs without rules.
- `tesla-valve` runs with the rules.
- `reshape` runs with the rules, and its prompt asks the agent to follow
  `skills/reshape/SKILL.md`. The skill waits for the user to pick the rows of
  its plan and to approve each slice, so the prompt approves them in advance.

The hidden tests of all six steps run before and after each refactor. The
plan, with what would count as a win, was written before the run:
[`refactor-plan.md`](games/refactor-plan.md).

```sh
python3 benchmark/games/refactor.py benchmark/games/results/20261010-1[23]*
python3 benchmark/games/pairwise.py benchmark/games/runs/refactor-<stamp> \
    --arms baseline,tesla-valve --judge claude-sonnet-5-5
python3 benchmark/games/pairwise.py benchmark/games/runs/refactor-<stamp> \
    --arms baseline,reshape --judge claude-sonnet-5-5
python3 benchmark/games/refactor.py --report benchmark/games/runs/refactor-<stamp>
```

The published refactoring runs:

| Run | Sources | Judge |
| --- | --- | --- |
| `refactor-20261010-173512` | the 24 projects of `gpt-6-luna` and `gpt-6.1-sol` | `claude-sonnet-5-5` |
| `refactor-20261010-173514` | the 8 projects of `claude-haiku-5-5` | `gpt-6.1-sol` |

Each record names its source. In `code.tar`, each refactor is one commit on
top of its source's history. Both Tesla Valve arms ran the rules as measured,
`tv-v7a`. The Codex session logs of these runs (29 MB) are
not published. From them and from Claude Code's own session files we counted
that every reshape session read the skill, and that no session of the
`tesla-valve` arm did.

## How the games were made

`gpt-6.1-sol` built each game from the brief in its `BRIEF.md`: the spec, the
steps, the fixtures, the hidden tests, the reference solutions, and the
deliberately broken references the selftest uses. The rules were frozen
before. We then read the selftest and the hidden tests, ran the selftest
ourselves, and edited the specs. `spec-edits.diff` in each game shows every
change:

- The spec no longer describes the finished game, because the agent sees it
  one section at a time. Wording that hinted at later steps went for the same
  reason.
- driftfall, section 3: "Pause and resume leave hold_available unchanged." The
  first run, `20261010-120039`, showed the spec did not say this. That run is
  the only one made without the sentence. The hidden-test totals of that run
  are not comparable with the later ones. Its verdicts compare two arms that
  saw the same spec.
- skirmish: "Write and flush each reply before reading the next line", added
  after a baseline-only pilot.

Three pilot runs are not published: the skirmish pilot, with the baseline arm
only, a one-cell check of the Claude sandbox, and a one-source check of
`refactor.py`.

## What is not here

RESULTS.md reports two side experiments, on bug fixes in open-source projects
and on one follow-up change. The rules round also used a guard set of small
one-off tasks. Their harnesses are tied to the machine they ran on and are not
part of this benchmark.
