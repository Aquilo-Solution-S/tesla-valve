# Tesla Valve

Build code like a Tesla valve: the right path is the path of least resistance,
and the wrong path works against itself. The measure is mental load per shipped
feature: someone who did not write the code understands it at first glance. A
guard, pin, fixture or proof that no feature needs is load, not safety.

## Before you write

Map the feature as streams: the path each piece of information takes from the
spring, where it enters the code, to the goal, where it is used.

1. Which streams does it need? Name every transformation on the way.
2. Which streams already flow? Join them at their contract. Never dig a second
   channel beside one: two sources of truth drift. Search the project before
   you build one: its logger beats a bare `print`. A channel you replace goes,
   with its tests and its guards, in the commit that adds the new one.
3. What does the language guarantee? Carry each stream in types, exhaustive
   matches, ownership and a single constructor. A convention is not a guarantee.

## While you write

- Shape over checks: make wrong use impossible to write instead of catching it
  when it runs. Contain instead of compare. A closed choice is a type, matched
  case by case, without a catch-all.
- If it exists, it is valid: the constructor is the only way in, and it returns
  the value or the reason it could not. No setter breaks it later, no cast
  forges one. Every way in counts: a default, a conversion from the raw value,
  a mutable accessor. Where you can, build the value from parts that cannot be
  wrong, an enum or a narrow integer, so no module has to be trusted to keep it
  valid.
- Check once, at the spring: data from a user, a file, the network, another
  system, the database or the clock is parsed into its type where it enters,
  and trusted from there. Read the clock at the spring and pass it in. Your own
  repository is not a spring: a hash pin, or a list of its own files, types or
  names that each change must extend, is only right while someone remembers
  it. Derive it from the tree or delete it.
- Facts about the world go stale: stock sells out, a token expires. A fact is
  not an invariant. Check it again where the operation commits, atomically
  with it: a conditional update, a constraint, a lock. A read and a later write
  is a race.
- A moving part is anything that is only right if someone remembers it,
  chooses it or times it: a flag, a call that must come first, a check that
  must sit in the right place. Remove the ones a shape can replace.

## On every check

When a finding says "add a check", or a diff adds a defensive comparison, first
ask whether a shape can make the mistake impossible.

- It can, and the shape weighs less than the check: change the shape, add the
  line that proves the wrong use does not compile where the toolchain checks
  one, and remove the check.
  Otherwise the check stays: a unit converter needs no Meter, Foot and
  Conversion types for one multiplication.
- It cannot, because the data comes from outside: the check goes to the spring,
  returns a typed result, and gets a test that feeds it the bad data.

One shape attempt per finding, and no reshaping beyond the task. A round of
critique that only rephrases is the last round.

## Tests

- Test the intent: what the code computes (a date, a price, a business rule)
  and what it guarantees across its parts (a reservation is released when the
  order is cancelled) keeps a test at the cheapest level that shows it.
- Tests build each value through one test constructor beside its type, which
  fills in defaults and builds it the way the code does. A new required field
  changes that constructor and the tests that care about the field, nothing
  else.
- Every check at a spring gets a test that feeds it the bad data. A test double
  is not a spring: its checks get no tests.
- Where the toolchain checks a line that must not compile (`compile_fail` in a
  Rust library, `@ts-expect-error`), one such line per shape another crate or
  package uses keeps the shape from being loosened unnoticed. The line is the
  proof, not a snapshot of the compiler's message. Where the toolchain does not
  check one, as in Go, a Rust binary crate or a crate with doctests turned off,
  the compiler alone holds the shape: no test runs the compiler, and no crate
  is split to get one.
- A test goes when the behaviour it pins goes, in the same commit, or when the
  compiler or a linter this project runs now catches what it caught: then name
  the shape that does.

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

Every line of a style guide, a review checklist or a prompt names its enforcer
(a type, a tool, a gate), or is a judgment call with its why and one example.
Delete the rest. A list each change must extend by hand is not an enforcer.
Whatever has to be remembered will be forgotten.
