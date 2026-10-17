# Refactoring: the plan, written before the run

Written on 10 October 2026 at 17:30 CEST, before any refactor session ran.

**Question.** When an agent refactors code it did not write, does Tesla Valve
make the result better to maintain, without changing what the code does and
without over-building it?

**Sources.** The 32 projects of the published runs that grew without rules
(arm `baseline`), as they stood after step 6. Each is refactored by the model
that grew it: 10 by `gpt-6.1-sol`, 14 by `gpt-6-luna`, 8 by `claude-haiku-5-5`.

**Arms.** Every source is refactored three times, each a fresh session followed
by CI with one fix round, as in the game benchmark:

- `baseline`: no rules.
- `tesla-valve`: the rules, delivered as in the game benchmark.
- `reshape`: the rules, and the prompt asks the agent to follow
  `skills/reshape/SKILL.md`, the way INSTALL.md tells an agent without slash
  commands to start it. The skill waits for the user to pick the rows of its
  plan and to approve each slice, so the prompt approves them in advance.

All three get the same task: refactor the project so the next change is easy
and safe to make, without changing what it does.

**Measures.**

1. *Design.* The blind pairwise judge of the game benchmark, unchanged: the
   `neutral` instructions, both orders, a judge from the other vendor
   (`claude-sonnet-5-5` for Codex authors, `gpt-6.1-sol` for Claude authors).
   Two comparisons: `tesla-valve` against `baseline`, and `reshape` against
   `baseline`.
2. *Behaviour.* The hidden tests of steps 1 to 6 run before and after. A
   refactor breaks a project when a hidden test that passed before fails after.
3. *Over-building.* The judge's flag, as in the game benchmark.
4. *Cost.* Agent time, output tokens, dollars, lines of code and of tests.

**What counts.** We say Tesla Valve helps refactoring only if, for that arm:

- the judge prefers it more often than `baseline`, with a two-sided sign test
  over the decisive pairs below 0.05;
- it breaks no more projects than `baseline`;
- the judge flags no more of its projects as over-built than of `baseline`.

Otherwise we report what happened. Either way the result goes into
RESULTS.md, with the numbers that go against us.

**What this does not test.** Whether a refactored project carries the next
features better. No step follows the refactor.
