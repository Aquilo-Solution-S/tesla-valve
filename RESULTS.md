# Does it work?

We measured it. In short:

- **Code that has to grow.** AI agents built two small games in six steps each,
  with Tesla Valve and without. A judge compared each pair blind. It preferred
  the Tesla Valve code in **28 of 32 comparisons**, the other code in 2, and
  called 2 a tie. That held for all three models that wrote the code.
- **Without over-building.** The judge also looked for over-built projects. It
  flagged none of the 64, on either side.
- **At a small cost.** The agents took a median 12% longer, and the code came
  out 4% longer, with as many lines of tests.
- **Refactoring: preferred, but over-built.** When agents refactored code that
  had grown without rules, the judge preferred the Tesla Valve result in 22 of
  32 pairs, against 8. But the strongest model over-built half of its
  refactors, so by the criteria we wrote down before the run, it is not a win.
- **What it does not do.** It did not make the code measurably more correct.
  On bug fixes in mature open-source projects it made no difference.

All runs date from 9 and 10 October 2026. The rules measured were frozen
before either game was written. They are the ones in this repository, but for
one line we narrowed after the refactoring experiment and a few we changed
after a week of use, as described there.
`benchmark/games/variants/v7a.patch` restores them. The benchmark is in
[`benchmark/`](benchmark), so you can run it yourself.

## Code that has to grow

The case Tesla Valve is built for is code that lives on: the next change comes
from someone who did not write the first version. So we let the code grow.

**The games.** Two small, fully deterministic games, written for this
benchmark, each with its own six-step specification:

- *driftfall*, a falling-blocks puzzle. The steps add pause, hold and preview,
  a new piece, a timed mode, and replaying a recorded game.
- *skirmish*, two squads on a 9×9 field with simultaneous turns. The steps add
  terrain costs, fog of war, a healer, terrain defence, and saving and loading
  a game.

Both are command-line programs that answer JSON requests, in Rust and in Go.
Some steps add features. Others change a rule the code already follows, such as
how far a unit can move or how much damage it deals. Some have consequences in
code the step's text does not mention. That is where a codebase shows whether
it carries a change or breaks under it.

**The run.** One agent builds step 1 from the specification. Then a fresh agent
session does each further step on the code it finds. It sees the specification
only up to its own step, so nobody can design for a feature that has not been
announced. After every step the project's CI runs: formatter, linter, the
agent's own tests. Then hidden tests drive the built program, the tests of
every step so far, so a broken old feature shows up. The two groups use the
same model and the same prompts. The only difference is whether Tesla Valve is
installed.

**The judgement.** The judge sees the specification and the final code of both
projects, labelled A and B. It is never told which is which. It is asked
which project it would rather receive to build the next feature and to
maintain for years. Then it judges the same pair again with A and B swapped. A
pair counts for a side only if both verdicts agree. If they disagree, it
counts as a tie. The judge is always a model from a
different vendor than the one that wrote the code. Its instructions do not use
Tesla Valve's vocabulary.

**The result.** Each pair is one game in one language, built twice by the same
model: once with Tesla Valve and once without.

| Model that wrote the code | Pairs | Tesla Valve preferred | Without preferred | Tie | Judge |
| --- | ---: | ---: | ---: | ---: | --- |
| `gpt-6.1-sol` (Codex) | 10 | 10 | 0 | 0 | `claude-sonnet-5-5` |
| `gpt-6-luna` (Codex) | 14 | 11 | 2 | 1 | `claude-sonnet-5-5` |
| `claude-haiku-5-5` | 8 | 7 | 0 | 1 | `gpt-6.1-sol` |
| **All** | **32** | **28** | **2** | **2** | |

Per game: driftfall 14 : 2 : 2 over 18 pairs, skirmish 14 : 0 : 0 over 14. Both
games were written after the rules were frozen. Skirmish was the second, built
as a fresh test.

The judge also marked any project it found over-built. It marked none of the
64 projects on either side.

If the rules made no difference, a split of 28 to 2 would come about by chance
less than once in a million (a simple sign test). The pairs share two games
and a handful of models, so read this as strong evidence on code like these
games, not as a law of nature.

**What the judges named.** Where Tesla Valve won, the reasons repeat:

- commands and game phases that are types, not strings;
- one path for live play and replay, instead of a second copy;
- one validation shared by every command that needs it;
- tests that check hidden state and that a query agrees with what actually
  happens.

On the other side: duplicated validation and attack logic, replay tangled into
input parsing, state that anything can change from outside.

Both losses were `gpt-6-luna` projects:

- In the Go one, the Tesla Valve side copied the replay logic instead of
  reusing the live path, which is the very thing the rules ask it not to do.
- In the Rust one, it sent every command through a convoluted parsing step
  built on anonymous tuples.

**The rules have to be there in every session.** In one variant, Tesla Valve
was present only while step 1 was built, and steps 2 to 6 ran without it. That
variant beat the plain one only 4 to 3, with 1 tie (judged by `gpt-6.1-sol`,
with an earlier version of the instructions that named the criteria). In our
runs a good start did not carry itself. The shape held where each session that
changed the code had the rules. The plugin loads them at the start of every
session.

## What it costs

Tesla Valve asks the agent to map the feature before it writes, and that takes
time. For each pair, the Tesla Valve project against the one without, the
median change:

| Model that wrote the code | Pairs | Agent time | Output tokens | Dollars | Lines of code | Lines of tests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gpt-6.1-sol` (Codex) | 10 | +12% | +11% | | +14% | +10% |
| `gpt-6-luna` (Codex) | 14 | +0% | −1% | | +0% | −8% |
| `claude-haiku-5-5` | 8 | +18% | | +50% | +6% | −1% |
| **All** | **32** | **+12%** | | | **+4%** | **+0%** |

- The agents with Tesla Valve took longer in 23 of the 32 pairs. A whole game,
  six steps with their fix rounds, took a median 10.5 minutes against 9.1 for
  `gpt-6.1-sol`, 5.3 against 5.0 for `gpt-6-luna`, and 18.1 against 14.9 for
  `claude-haiku-5-5`. That is the agent's own time, without CI and the hidden
  tests.
- Codex reports output tokens but no price, Claude Code a price but, in our
  harness, no tokens. A `claude-haiku-5-5` game cost a median $0.49 with Tesla
  Valve and $0.31 without.
- Lines are non-empty lines of Rust and Go in the final project. A file named
  for tests, and in Rust everything from `#[cfg(test)]` on, counts as tests.

`benchmark/games/cost.py` computes the table from the published runs.

## Refactoring code it did not write

The games measure code that grows with Tesla Valve from its first line. Most
code does not start that way. So we took the 32 projects that grew without it,
as they stood after step 6, and had the model that grew each one refactor it,
three times:

- without rules;
- with the rules;
- with the rules, and asked to follow the
  [`reshape`](skills/reshape/SKILL.md) skill. The skill waits for the user to
  approve its plan and each step, so the prompt approved them in advance.

All three got the same task: refactor the project so that the next change is
easy and safe to make, without changing what it does. Before the run, we wrote
down what would count as a win: [the plan](benchmark/games/refactor-plan.md).

Others have measured agents that refactor.
[RefactorBench](https://arxiv.org/abs/2503.07832) asks whether they complete
refactorings across many files at all. Two studies of agents' changes in
open-source projects, by [Horikawa et al.](https://arxiv.org/abs/2511.04824)
and [Ottenhof et al.](https://arxiv.org/abs/2601.20160), found their
refactorings mostly low-level: a renamed parameter, a changed type, an
annotation. We asked something narrower: whether a set of rules changes the
design an agent leaves behind.

| Model that refactored | Pairs | With the rules | With reshape | Judge |
| --- | ---: | :---: | :---: | --- |
| `gpt-6.1-sol` (Codex) | 10 | 6 : 2 : 2 | 7 : 1 : 2 | `claude-sonnet-5-5` |
| `gpt-6-luna` (Codex) | 14 | 11 : 3 : 0 | 9 : 2 : 3 | `claude-sonnet-5-5` |
| `claude-haiku-5-5` | 8 | 5 : 3 : 0 | 5 : 2 : 1 | `gpt-6.1-sol` |
| **All** | **32** | **22 : 8 : 2** | **21 : 5 : 6** | |

Each cell reads Tesla Valve preferred : without preferred : tie, against the
refactor without rules, judged as in the games. Both splits would come about
by chance less than once in fifty (a sign test).

**No refactor changed what a program does.** Every hidden test that passed
before a refactor passed after it, in all three arms. The run itself recorded
one reshape refactor that broke five tests, and one with the rules that made
three pass. Run again one at a time, neither held. The five passed: the hidden
tests give each reply two seconds, and while nine agents and their builds
shared the machine, their replies came too late. The three failed again,
before the refactor and after it. `refactor.py --recheck` runs them all again.

The plan asked for one more condition, and it failed.

**It over-built.** The judge flagged 5 of the refactors with the rules as
over-built, and 7 with reshape, against none without rules. All of them were
`gpt-6.1-sol`'s, and every flag named tests that prove a wrong use does not
compile. The rules ask for one line per shape that proves this. Rust runs such
a line only as a documentation test of a library, Go has none, and these games
are programs, not libraries. So in 10 of the 12 flagged projects a test ran
the compiler or a type checker itself. The other 2 had split the program into
a library, where documentation tests run, and the judge still called them
ceremony. In the games, `gpt-6.1-sol` wrote such tests in 2 of its 10
projects. In the refactors it wrote them in 7 of 10 with the rules, and in all
10 with reshape, which asks for that line in every step. Three of reshape's
flags also named a type the judge found heavier than the game needed.

So by our own criteria, we do not claim that Tesla Valve helps refactoring.
The preference is clear, and the weakness is specific: the rule asks for a
proof that the wrong use does not compile, even where the language has no
cheap way to write one.

We have since narrowed that line. It is written only where the toolchain
checks it, such as a `compile_fail` doc test in a Rust library or
`@ts-expect-error` in TypeScript. Where it is not, as in Go or a Rust program,
the compiler alone holds the shape, and nothing is built to prove it. This
change is not measured yet. Every number on this page comes from the rules
before it.

After a week of using the rules on our own code, we changed a few more lines.
The agents had pinned their own repository with hashes and hand-kept lists,
spelled out the same values in dozens of tests, snapshotted compiler messages
as proofs, and kept old tests alive beside the code that replaced them. So the
measure now counts a guard, pin, fixture or proof that no feature needs as
load; the repository is not a spring; tests build values through one test
constructor per type; a proof is the line that does not compile, never a
snapshot of the message; and a test leaves with the behaviour it pins. These
changes are not measured either.

Refactoring with the rules took longer for the Codex models. A refactor by
`gpt-6.1-sol` took a median 2.7 minutes without rules, 4.1 with them and 6.1
with reshape. `gpt-6-luna` took 0.7, 0.8 and 1.7 minutes, and
`claude-haiku-5-5` 6.7, 6.7 and 7.3. The code came out between 2% shorter and
12% longer. In every reshape session the agent read the skill, and in no
session with the rules alone did it.

## What this does not show

- **That the code is more correct.** The hidden game tests give no consistent
  answer. The strongest models passed nearly everything either way.
  `gpt-6-luna` was noisy. On skirmish, more of its steps passed every hidden
  test with Tesla Valve (21 of 36) than without (10 of 36). Yet its Go projects
  with Tesla Valve passed fewer tests: 68% against 96% after the last step.
  That was mostly one project, whose default game built its units through a
  second path that never set their hit points, which broke almost every test.
  That is exactly the mistake rule 3, *if it exists, it is valid*, is there to
  prevent. The rule was in the agent's context, and the agent did not follow
  it.
- **That it helps everywhere.** Two side experiments found no difference.
  Their harnesses are tied to the machine they ran on and are not part of
  [`benchmark/`](benchmark).
  - *Bug fixes in mature open-source code.* `gpt-6.1-sol` fixed 44 real issues
    from Rust and Go projects (SWE-rebench, May and June 2026). Both groups
    fixed 25. A blind design judge split 17 to 14, with 12 ties. A small fix in
    a codebase that already has its shapes leaves little room for design.
  - *One follow-up change.* A second agent changed code a first agent had
    built. It succeeded or failed about equally often in both groups. Here the
    benefit of the shapes showed in what judges read, not in what tests caught.
- **That a refactor carries the next feature.** No step followed the
  refactors. In the games, a good start did not carry itself.
- **How fast the code decays.** We compared the code after the sixth step.
  [SlopCodeBench](https://arxiv.org/abs/2603.24755) measures the quality of
  agent code at every step as it grows. It found that quality instructions in
  every session made the first version cleaner, but did not slow the decline
  after it. We did not measure the decline, only where it ended.
- **That people agree.** The judges are AI models, not engineers. We judged
  every pair blind and in both orders, used a judge from a different vendor
  than the author, and kept Tesla Valve's own words out of the judge's
  instructions. On driftfall, `claude-sonnet-5-5` and `gpt-6.1-sol` agreed: 11
  to 2 and 12 to 2.
- **That it holds for every kind of software.** There are two games, both
  deterministic programs speaking JSON, both written for this benchmark. A web
  service or a data pipeline is a different test.
- **That nobody had a stake.** We wrote both the rules and the benchmark. To
  limit that:
  - the rules were frozen before the games existed;
  - the last decision about changing the rules followed criteria written down
    before the run;
  - we report the results that went against us.

## We tried to improve it, and failed

After the first game, the judges' complaints pointed at three weaknesses:

- replay logic copied instead of reused;
- input parsed into anonymous tuples;
- tests that could not fail.

We wrote a candidate with three added lines for these. Before running it, we
wrote down when it would replace the current rules: more wins than losses
against them on the second game, no more broken earlier steps, and no real
increase in over-building on a set of small one-off tasks.

The candidate broke 2 earlier steps where the current rules broke none. The
judge split 3 to 2 between the two versions, with 5 ties. Its two losses came
on the same kinds of weakness it was written to fix: copied validation and an
unnamed tuple. We dropped it.

The rules that held are the ones in this repository, but for the lines
changed since: the one narrowed after the refactoring experiment, and the few
changed after a week of use.
