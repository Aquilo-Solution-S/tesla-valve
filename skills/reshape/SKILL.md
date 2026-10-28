---
name: reshape
description: >
  Reshape existing code the Tesla Valve way: checks become shapes or move to
  the spring, and the tests the compiler now covers go, one stream at a time.
  Run it only when the user asks for it, on a scope the user names: it changes
  code beyond any one task.
disable-model-invocation: true
---

# Reshape

The tesla-valve skill reshapes only the code a task touches, so existing code
keeps its checks until someone asks for more. This skill is that ask. It holds
no rules of its own: every decision below follows the
[tesla-valve skill](../tesla-valve/SKILL.md) and the reference for the
language. Read them first.

## 1. Scope and enforcers

Work in the scope the user names: a module, a directory, a stream. Never the
whole repository at once.

Find out which enforcers the project runs, in its config and its CI. A check or
a test goes only where its replacement is enforced. Where an enforcer is
missing, the checks it would replace stay: name them, and suggest the prepare
skill. Configs and CI do not change here.

## 2. Inventory

List every check and every test of shape in the scope.

- The linters find part of it, and each finding names its rule. The prepare
  report lists the findings that keep a rule off.
- Read for what no linter sees: a closed choice compared as a string, a
  `validate()` called after construction, a value the type leaves optional but
  one state needs, a record parsed loose and checked field by field, a derived
  default, a conversion that cannot fail or a mutable accessor on a type with
  an invariant, a test that tests only shape.

## 3. Plan

One row per check, written down before any change. The kind is one of the
three in the tesla-valve skill, or "stays" when no shape holds without a
paragraph of explanation, or when its enforcer is missing. For the loose
`delivery_date` in the
[manifesto](https://github.com/Aquilo-Solution-S/tesla-valve/blob/main/MANIFESTO.md#one-step-in-code):

| check | kind | becomes | held by | tests |
| --- | --- | --- | --- | --- |
| `panic!("unknown stock status")` | bad data | `stock_of` refuses it | serde: unknown variant | a spring test feeds it an unknown status |
| `panic!("backorder without restock days")` | wrong use | `Backorder { restock_days: u16 }` | the compiler: a missing field | its test goes; a spring test feeds a backorder without days |
| `"in_stock"` spelled at every match | wrong use | `enum Stock`, matched without `_` | the compiler; clippy | its test goes |

The user picks the rows.

## 4. One stream per slice

A slice moves one stream: its type, its spring and its callers.

- The tests pass before the slice and after it. A slice changes how the code is
  shaped, never what it computes.
- Add first: the spring test that feeds the bad data, and, where the toolchain
  checks one, the line that proves the wrong use does not compile. Delete
  second: the check, and each test the shape now covers, naming the enforcer
  that does.
- After each slice, show the diff and the checks passing, and go on when the
  user agrees.

## 5. Slices of their own

- **A stale fact.** Moving its check to where the operation commits changes
  what happens when two callers race, so it is a fix, not a reshape. It gets a
  slice of its own and a test of the intent: two orders for the last item, and
  one of them succeeds.
- **A public API.** A narrower type in a public signature breaks the callers
  outside the repository. Add the typed function beside the old one, let the
  old one parse and call it, mark it deprecated, and name the breaking change
  for the next major version. Where untyped code calls in, the runtime check
  stays.

## 6. Report

One line per row of the plan, not per test: what the check was, and what holds
it now (a shape, the spring, the commit), or why it stays.
