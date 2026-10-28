---
name: tesla-valve
description: >
  Build code like a Tesla valve: wrong use impossible to write instead of
  caught when it runs, data from outside checked once where it enters, and
  tests for what the code is for. Use on any coding task (planning, writing,
  fixing, refactoring, reviewing), when a finding says "add a check", when a
  diff adds a defensive comparison, and when writing a style guide, a review
  checklist or a prompt.
---

# Tesla Valve

A Tesla valve is a channel with no moving parts: water passes freely one way,
and flowing back, the shape turns it against itself. Build code the same way.
The right path is the path of least resistance, and the wrong path works
against itself. The measure is mental load per shipped feature: someone who
did not write the code understands it at first glance. A guard, pin, fixture or
proof that no feature needs is load, not safety.

The reasoning behind every rule here is in the
[manifesto](https://github.com/Aquilo-Solution-S/tesla-valve/blob/main/MANIFESTO.md).

## Before the first line

Map the feature as streams. A stream is the path one piece of information takes
from the spring, where it enters the code, to the goal, where it is used.

1. **Which streams does it need?** Name every transformation on the way.
2. **Which streams already flow?** Join them at their contract. Never dig a
   second channel beside one: two sources of truth drift, and that is the one
   fault no type can catch. Search the project before you build one: its
   logger beats a bare `print`. A channel you replace goes, with its tests and
   its guards, in the commit that adds the new one.
3. **What does the language guarantee?** Carry each stream in types, exhaustive
   matches, ownership and a single constructor. A convention is not a
   guarantee.

For a new feature or a new stream, write the answers down before the code, in
your own notes, never in a commit, issue or report:

```text
feature     show the delivery date at checkout
goal        checkout page              Date

stream      postcode                                         new
  spring    checkout form              text                  outside
  check     Postcode::parse            text → Postcode | Invalid
  refused   Invalid                    back to the form, which says why
stream      stock                                            already flows
  spring    warehouse                  JSON                  outside
  join      stock_of                   JSON → Stock | Invalid
stream      today                                            new
  spring    clock                      Date                  outside
confluence  delivery_date              Postcode, Stock, Date → Date
```

Every spring from outside has a check, and every check says where its refusals
go. The map is a plan, not documentation: once the code exists it says the same
thing, so the map goes.

## While you write

- **Shape over checks.** Make wrong use impossible to write instead of catching
  it when it runs. Contain instead of compare. A closed choice is a type,
  matched case by case, without a catch-all.
- **If it exists, it is valid.** The constructor is the only way in, and it
  returns the value or the reason it could not. No setter breaks it later, no
  cast forges one. Nobody checks it again. Every way in counts: a default, a
  conversion from the raw value, a mutable accessor. Where you can, build the
  value from parts that cannot be wrong, an enum or a narrow integer, so no
  module has to be trusted to keep it valid.
- **Check once, at the spring.** Data from a user, a file, the network, another
  system, the database or the clock is parsed into its type where it enters,
  and trusted from there. Read the clock at the spring and pass it in. Your own
  repository is not a spring: a hash pin, or a list of its own files, types or
  names that each change must extend, is only right while someone remembers
  it. Derive it from the tree or delete it. A checksum file over the migrations
  directory changes with every migration; the migration tool's own record of
  what it applied does not.
- **Facts about the world go stale.** Stock sells out, a token expires. A fact
  is not an invariant. Check it again where the operation commits, atomically
  with it: a conditional update, a constraint, a lock. A read and a later write
  is a race.
- **Remove moving parts.** A moving part is anything that is only right if
  someone remembers it, chooses it or times it: a flag, a call that must come
  first, a check that must sit in the right place.

The shapes and their enforcers differ by language. Before writing code, read
the reference for its language: [Rust](references/rust.md),
[Go](references/go.md), [TypeScript](references/typescript.md) or
[Python](references/python.md).

Before trusting a shape, find its enforcer in the project's config and CI.
Where it is missing, keep the check, and tell the user that the prepare skill
sets it up. Do not change tools, configs or CI in the middle of a task.

## On every check

For each check a diff adds or a finding asks for, decide which of three it is:

1. **Wrong use:** a caller doing what the design never meant. Where the shape
   weighs less than the check, change the shape so it cannot be written, add
   the line that proves it does not compile where the toolchain checks one, and
   remove the check. Otherwise
   the check stays: a unit converter needs no Meter, Foot and Conversion types
   for one multiplication.
2. **Bad data:** something from outside that no type can see. The check goes to
   the spring, returns a typed result, and gets a test that feeds it the bad
   data.
3. **A stale fact:** the world changed since it was read. Check it where the
   operation commits, atomically with it.

A result can also fail on valid inputs: a sum overflows, a date runs past the
calendar. Bound the inputs at the spring so the type rules it out, the way
`restock_days: u16` does. Where no bound holds, return a typed failure where it
happens.

Make one shape attempt per finding. If no shape holds without a paragraph of
explanation, keep a plain check at the spring. Do not reshape code beyond the
task; where more would pay off, tell the user that the reshape skill does it.
A round of critique that only rephrases is the last round.

## Tests

A test has three homes:

- **The intent:** what the code computes (a date, a price, a business rule)
  and what it guarantees across its parts (a reservation is released when the
  order is cancelled) keeps a test at the cheapest level that shows it, often a
  plain unit test. Types remove the tests of shape, not the tests of meaning.
  Protocols, atomicity and failure recovery are intent: no local type proves
  them.
- **The spring:** every check there gets a test that feeds it the bad data. A
  test double is not a spring: its checks get no tests.
- **The shape:** where the toolchain checks a line that must not compile, one
  minimal line per shape another crate or package uses proves the wrong use
  still does not compile, so the shape cannot be loosened unnoticed. Keep it to
  the one line, so no unrelated error can satisfy it. The line is the proof,
  not a snapshot of the compiler's message: the message changes with the
  compiler. Where the toolchain has no such check, as in Go, a Rust binary
  crate or a crate with doctests turned off, the compiler alone holds the
  shape: no test runs the compiler or a type checker, and no crate is split to
  get one.

Any other test of shape marks unfinished landscape: no clean shape yet, an
unclear rule, an ambiguity, something implicit. A test goes when the behaviour
it pins goes, in the same commit, or when the compiler or a linter this project
runs now catches what it caught: then name the shape that does.

Tests build each value through one test constructor beside its type, which
fills in defaults and builds it the way the code does. A new required field
changes that constructor and the tests that care about the field, nothing else.
Forty tests that each spell out `Order { … }` all change when `Order` gains a
field; forty that call the test constructor do not.

## Where the shape stops

- Keep the runtime check wherever types are erased: deserialization, and any
  API that untyped code can call.
- A set owned elsewhere can grow. Parse it at the spring, and give what you do
  not know a typed refusal or an explicit unknown, never a silent default.
- A value with no invariant stays a primitive.
- A shape counts only where this project's compiler or CI enforces it. Where
  nothing does, keep the check.
- A type that needs a paragraph of comment to be understood loses to a plain
  check at the spring.
- A shape costs its fixtures and proofs, and pays where a mistake can travel:
  into another module, across a boundary, into a later change. In a one-file
  script or a demo it only adds load: keep the code plain, but keep the check
  of outside data at the spring and a test of what the code computes. A script
  that prunes old backups needs no Backup type around a file name, and still a
  test that it keeps the newest seven.

## Rules you write

Every line of a style guide, a review checklist or a prompt is one of three:

- **Enforced:** name the type, tool or gate that refuses the wrong version.
  A list each change must extend by hand is not an enforcer.
- **Could be enforced:** name the gate to build.
- **Judgment:** keep its why and one example.

Delete the rest, but convert before cutting: a rule usually came from a real
failure. Whatever has to be remembered will be forgotten.

## When you reply

If the change added, moved or removed checks or tests, end with one line per
shape or spring, not per test: what moved, and what holds it now (a shape, the
spring, or the commit).
