---
name: prepare
description: >
  Prepare a project for Tesla Valve: install the compiler settings, linters and
  CI steps that enforce its shapes, and prove that each one fires. Run it only
  when the user asks for it, once per project and again when a language is
  added: it writes configs and CI.
disable-model-invocation: true
---

# Prepare

The tesla-valve skill trusts a shape only where the project's compiler or CI
enforces it. Everywhere else it keeps the runtime check. This skill puts the
enforcers in place, once, and proves that each one fires, so the shapes start
to count.

It changes the project's configs and CI, so it runs only when the user asks,
never in the middle of another task.

## 1. Survey

Find the languages the project builds (`Cargo.toml`, `go.mod`,
`pyproject.toml`, `package.json` with `tsconfig.json`), and read the reference
for each: [Rust](references/rust.md), [Go](references/go.md),
[TypeScript](references/typescript.md), [Python](references/python.md).

For each enforcer in the reference, find out whether the project has it, lacks
it, or has it weaker: `strict` off, `default-signifies-exhaustive: true`, a
lint set to warn where CI does not fail on warnings. Find the CI the project
already runs and what it calls.

Show the survey as a table before changing anything: enforcer, state, file.

## 2. Propose

- One diff per file, merged into what is there. Never replace a config whole,
  and never drop a rule the project already has.
- Where the project already runs another tool for the same job, such as Biome
  instead of ESLint, look for its rule first and prove it the same way. Add a
  second tool only for what the first cannot hold.
- Pin every new tool the way the project pins the rest: a lockfile, a
  requirements file, `go install ...@version`.
- Count each new rule's findings on the existing code, in a temporary copy
  with the proposed config, and with any missing tool installed outside the
  project. A rule with findings stays off for now: the report lists them for
  the reshape skill, and a later run of prepare turns the rule on once they
  are gone. Until then its shape does not count, and the checks it would
  replace stay.
- Change nothing until the user agrees to the diff.

## 3. Wire into CI

Add the commands to the CI the project already runs, in the style of its other
steps. A failed check must fail the build. Add no new CI system.

## 4. Prove that each enforcer fires

A config that loads but enforces nothing looks the same as one that works. For
each enforcer:

1. Copy the project to a temporary directory, without build output.
2. Add one small file that breaks exactly that rule. Each reference shows one
   per enforcer; rewrite it in the project's own types.
3. Run the checks. They must fail, and the output must name the rule or the
   error code the file's `expect:` line gives.
4. Delete the copy. The bad file never enters the project.

Match on the tool's message, not on your own comment: leave the `expect:` line
out of the copy, because some tools print the source they refuse.

## 5. Report

One line per enforcer: what it holds, and whether it is now on and proven. Then
the shapes that do not count yet, because their enforcer is off or its proof
failed, with the findings that keep each rule off. Their runtime checks stay
until it is on.
