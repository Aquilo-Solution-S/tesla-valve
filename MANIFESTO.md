# The Tesla Valve Manifesto

<p align="center">
  <img src="assets/tesla-valve.svg" alt="A Tesla valve. Water flows freely from left to right. Flowing back, every loop turns it against itself.">
</p>

Information should flow like water. Water always finds its destination, drawn
by the gentle, unyielding pull of gravity.

- **The goal is gravity:** the one steady pull every drop answers to.
- **The code is the landscape:** it guides the information the way terrain
  guides water.
- **The source is the spring:** the point where information enters the code.

A Tesla valve is a channel with no moving parts. Water passes through it freely
in one direction. Flowing back, the shape of the channel turns the water
against itself. Nothing has to be opened, closed or remembered. Code should
carry information the same way: the right path is the path of least
resistance, and the wrong path works against itself.

It does not have to be perfect. A real Tesla valve leaks a little, and so does
code: a cast, an `any`, an `unsafe`. What matters is that the direction of flow
feels natural. The right way is the easy way, and the wrong way takes a
deliberate effort that everyone can see.

## The rules

1. **Only parts that do not move can be trusted.** This holds in every field of
   engineering. A moving part is anything that is only right if someone
   remembers it, chooses it or times it: a flag, a call that must come first, a
   check that must sit in the right place. Each one can stick, wear out or be
   skipped. A fuse does not move in this sense, nor does a transaction: nobody
   has to remember them. A `validated` flag on a postcode moves. A `Postcode`
   that cannot exist unless it is valid does not. The other rules follow from
   this one.
2. **Shape over checks.** Make wrong use impossible to write instead of catching
   it when it runs. Contain instead of compare. A closed choice as a type,
   matched case by case, without a catch-all. A check kept beside a shape that
   already forbids the misuse is dead code, and it documents a path that does
   not exist.
3. **If it exists, it is valid.** It met its invariants when it was built, and
   nothing breaks them afterwards. The constructor is the only way in, and it
   refuses everything invalid: it returns the object or the reason it could
   not. There is no setter to break the object later, and a cast that forges
   one is a hole in the landscape. Nobody checks an object once it exists. A
   fact about the world is not one of its invariants: that is rule 4.
4. **Check once, at the spring.** Only data from outside can be wrong in a way
   no type can see: from a user, a file, the network, another system, the
   database, the clock. Check it where it enters, by constructing the type it
   becomes, and trust it from there. A fact about the world goes stale, though:
   stock sells out, a carrier stops delivering, a token expires. Every reading
   of the world is a spring of its own, and the reading that counts is the one
   where the operation commits, atomically with it: a conditional update, a
   constraint, a lock. A read and a later write is a race.
5. **Test the intent, not the code.** What the code does is the shape's job.
   What the code is for is the test's job. That a backorder carries its restock
   days is shape. That an order placed on Tuesday arrives on Thursday is
   intent.
6. **Mental load, not lines of code.** Slop is not measured in lines. The
   measure is: does someone who did not write it understand it at first
   glance? Lines still count where nothing needs them: a guard, a pin, a
   fixture or a proof that no feature needs is load, not safety. A type that
   needs a paragraph of comment to be understood loses to a plain check at the
   spring.
7. **A rule names its enforcer, or carries its why, or goes.** Style guides,
   review checklists, the rules we give AI: each line is enforced by a type, a
   tool or a gate, or it is a judgment call with its reason and one example.
   Whatever has to be remembered will be forgotten. This manifesto is held to
   it too: rules 2 to 4 name their enforcers under
   [Hard and soft languages](#hard-and-soft-languages), and the others are
   judgment, each with its example.

## Before the first line

Every feature starts with three questions.

1. **Which streams does it need?** A stream is the path one piece of
   information takes from the spring, where it enters, to the goal, where it is
   used. Name every transformation on the way. A feature is a set of streams.
2. **Which streams already flow?** Join an existing stream at its contract
   instead of digging a second channel beside it. Two channels carrying the
   same information are two sources of truth, and drift between them is the one
   fault no type can catch.
3. **What does the language guarantee?** Carry each stream in what the compiler
   enforces: types, exhaustive matches, ownership, a single constructor. That is
   bedrock, and bedrock needs no test. A convention is not a guarantee.

One feature, traced: show the delivery date at checkout.

<p align="center">
  <img src="assets/streams.svg" alt="Three streams for one feature. A postcode from the checkout form is checked once and becomes a Postcode; what fails the check goes back to the form. The warehouse's stock already flows through stock_of and is joined, not dug again. The clock gives today's date. All three meet in delivery_date, which gives the checkout a Date.">
</p>

Written down, the answers are the plan:

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

The postcode comes from outside, so it is checked once, at the spring, and is a
`Postcode` from then on. What fails the check goes back to the form. The stock
already flows to the cart page, so we join it instead of digging a second
channel beside it. The clock is a spring too: today's date is read once, where
the request starts, and passed in. We write two functions, `Postcode::parse`
and `delivery_date`. Everything else already flows.

The map is a plan, not documentation. Once the code exists it says the same
thing, and two places saying one thing will drift, so the map goes.

Then implement and critique. The implementation follows the plan downhill. The
critique is the valve: a finding that says "add a check" is first asked whether
the shape can make the mistake impossible. If it can, the shape changes and the
check is never written. If it cannot, the check goes to the spring, with a test
that feeds it the bad data. A round of critique that only rephrases is the last
round.

That is what AI is for: finding the natural course of the logic we build, not
raising cathedrals of complexity.

## Test the intent, not the code

Bad code attracts bad tests. Good code attracts good tests. Perfect code would
need no tests of its shape at all, only of its intent: does what enters at the
spring arrive at the goal, and arrive right?

Types remove the tests of shape, not the tests of meaning. A delivery date, a
price, a business rule: what the code computes is intent. So is what it
guarantees across its parts, which no local type can prove: a reservation is
released when the order is cancelled, a failed payment leaves no order behind.
Intent is tested at the cheapest level that shows it, often a plain unit test.

Beside the intent, a test has two more homes: the spring, where it feeds in the
bad data the check must refuse, and the shape, where one line proves that the
wrong use still does not compile, so the shape cannot be loosened unnoticed.
That line exists only where the toolchain checks it: a `compile_fail` doc test
in a Rust library, `@ts-expect-error` in TypeScript. In Go, in a Rust program
without a library, and in a library whose doc tests are off, the compiler alone
holds the shape, and nothing is
built to prove it. Any other test of shape marks unfinished landscape:

- where we found no clean way to move information from A to B in the shape of a
  Tesla valve,
- where the rules are not clear,
- where something is ambiguous,
- where we act implicitly instead of explicitly.

Such a test goes when the compiler, or a linter the project runs, catches what
it caught. And every test goes with the behaviour it pins: when a path is
replaced, its tests leave in the commit that replaces it.

Tests are code too. Past a certain number they would need tests of their own,
and if we are honest, hardly anyone reads them. Every check is a second place
where a decision lives: it can be wrong, go stale or be bypassed.

## One step, in code

The code is Rust, because Rust holds what it promises. Other languages follow
below.

Zoom into the confluence, `delivery_date`. Here it is the way it often gets
written: it digs its own channel to the warehouse and reads stock the way the
warehouse sends it, as a loose record.

<!-- code: examples/rust/src/before.rs#before -->
```rust
pub struct WarehouseStock {
    status: String,
    restock_days: Option<u64>,
}

pub fn delivery_date(postcode: &Postcode, stock: &WarehouseStock, today: NaiveDate) -> NaiveDate {
    let days = match stock.status.as_str() {
        "in_stock" => shipping_days(postcode),
        "backorder" => match stock.restock_days {
            Some(restock_days) => restock_days + shipping_days(postcode),
            None => panic!("backorder without restock days"),
        },
        other => panic!("unknown stock status: {other}"),
    };
    today + Days::new(days)
}
```

Three checks, and each needs its tests: an unknown status, a backorder without
restock days, a status spelled one way here and another way at the warehouse.
Each is a moving part, and each repeats a decision `stock_of` already makes.
Two places now decide what stock means, and they will drift.

Now join the stream that already flows. `stock_of` reads the warehouse's JSON
into a `Stock`, a closed choice:

<!-- code: examples/rust/src/lib.rs#stock -->
```rust
#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case")]
pub enum Stock {
    InStock,
    Backorder { restock_days: u16 },
}

pub fn delivery_date(postcode: &Postcode, stock: Stock, today: NaiveDate) -> NaiveDate {
    let days = match stock {
        Stock::InStock => shipping_days(postcode),
        Stock::Backorder { restock_days } => u64::from(restock_days) + shipping_days(postcode),
    };
    today + Days::new(days)
}
```

Nothing is left to check. A backorder without restock days cannot be built, a
misspelled kind does not compile, and restock days are a `u16`: never negative,
never above 65,535, so the sum cannot overflow. The day we add a third kind,
say `Discontinued`, the build stops at every `match` that has not decided what
it means. Only a `_` arm could hide it, and clippy can forbid that.

A new status from the warehouse is a different matter. That is not our code
changing, it is the world, and the world is checked at the spring. The derive
turns the type into the check: `stock_of` refuses `discontinued` with "unknown
variant `discontinued`, expected `in_stock` or `backorder`", a backorder
without its days with "missing field `restock_days`", and 70,000 days with
"invalid value: integer `70000`, expected u16". The checks have become
laws of nature, written where everyone can see them. A mistake in our code
shows up when it compiles, not when a test happens to run.

`Postcode` is built the same way. Its constructor is the gate at the spring, and
the only way in:

<!-- code: examples/rust/src/postcode.rs#postcode -->
````rust
/// Five digits. The only way to get one is `Postcode::parse`:
///
/// ```
/// assert!(shop::Postcode::parse("10115").is_ok());
/// ```
///
/// ```compile_fail
/// shop::Postcode(String::from("hello"));
/// ```
///
/// ```compile_fail
/// let _: shop::Postcode = Default::default();
/// ```
///
/// ```compile_fail
/// let _ = shop::Postcode::from(String::from("hello"));
/// ```
pub struct Postcode(String);

impl Postcode {
    pub fn parse(raw: &str) -> Result<Postcode, Invalid> {
        let code = raw.trim();
        if code.len() == 5 && code.bytes().all(|b| b.is_ascii_digit()) {
            Ok(Postcode(code.to_owned()))
        } else {
            Err(Invalid("a postcode is five digits"))
        }
    }
}
````

The field is private, so outside its module `Postcode(...)` does not compile.
The second doc test proves it, and fails the day someone makes the field
public. The first one compiles the same path, so a misspelled name cannot make
the second one pass. So `delivery_date` never asks whether its postcode is
valid. If it exists, it is valid: five digits, which is all a `Postcode`
promises. Whether a carrier delivers there is a fact about the world. It can
change tomorrow, so it is checked where the order is placed.

What is left to test is what no type can know: whether the date is right.

<!-- code: examples/rust/src/lib.rs#intent -->
```rust
#[test]
fn ordered_on_tuesday_arrives_on_thursday() {
    let tuesday = date(2026, 10, 6);
    let berlin = Postcode::parse("10115").unwrap();
    let arrives = delivery_date(&berlin, Stock::InStock, tuesday);
    assert_eq!(arrives, date(2026, 10, 8));
}
```

That is the whole suite for this step: this test of intent and one for a
backorder, the bad data fed in at both springs, and the doc tests that hold the
shapes. The three checks of the loose version are gone, and so are their
tests, because the compiler now catches what they caught. All of it runs in
[the Rust example](examples/rust).

## Hard and soft languages

Rules 2 to 4 have enforcers, and which ones depends on the language:

| | 2. Shape over checks | 3. If it exists, it is valid | 4. Check once, at the spring |
| --- | --- | --- | --- |
| Rust | an exhaustive `match`; clippy forbids the `_` arm | private fields; in a library, a `compile_fail` doc test that tries to forge one | `serde`, `TryFrom` or `FromStr` into the type |
| Go | an interface closed by convention, or a named type, switched case by case; `gochecksumtype` and `exhaustive` hold it | unexported fields, and `ParseX` as the only way in | a wire struct, then a parse function into the type |
| TypeScript | `switch-exhaustiveness-check`, and `default` calls `unreachable(x: never)` | a private constructor; no `as`, no `any` | a runtime parser at every boundary, such as zod |
| Python | `match` with `case _: assert_never(x)`, under pyright strict or mypy | a constructor that refuses, and `frozen=True`; no `cast`, no `Any` | a strict pydantic model at every boundary |

Go's lint rules are golangci-lint's, TypeScript's are typescript-eslint's under
`strict`, and Python's are ruff's. Each language has a reference in the skill,
its setup in the prepare skill, and [an example](examples) that CI runs: the
example must pass clean, and every enforcer in this table is fed a file it must
refuse.

Rust is bedrock. Its guarantees still hold while the code runs, and stepping
outside them takes a word everyone can see, such as `unsafe`. Go is firm ground
with holes. The compiler checks every type and an unexported field is truly
private, but every type has a zero value that nobody constructed, an interface
can be nil, and a closed choice is closed by a linter, not by the language.
Where a zero value would flow on and do harm, Go keeps the check.

TypeScript and Python are softer ground. TypeScript's types are erased when the
code runs, and plain types match by shape, not by name. Python's types are
hints that nothing checks while it runs. In both, an `any` or a cast passes
through every wall. In soft ground a channel holds only where it is lined: a
checker in strict mode, and a tool that forbids the leaks. And wherever the
types are gone, at a public API that untyped code can call or at data read from
JSON, the runtime check stays.

## Where it comes from

The core is not new. Rules 2 and 3 are Yaron Minsky's *make illegal states
unrepresentable*, from his 2010 talk on effective ML, written up as
[Effective ML Revisited](https://blog.janestreet.com/effective-ml-revisited/).
Rule 4 is Alexis King's
[Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/):
check the data once, where it enters, by turning it into a type that keeps
what the check found. Her
[Names are not type safety](https://lexi-lambda.github.io/blog/2020/11/01/names-are-not-type-safety/)
draws the line rule 3 leans on: a value behind a constructor is only as safe as
the module that builds it, while one built from parts that cannot be wrong
needs no trusted module at all.

What Tesla Valve adds is for the agent that writes the code. A shape counts
only where something enforces it, so every rule names its enforcer, and the
prepare skill sets the enforcers up before a shape relies on them. The rules
say where a shape stops, so a plain check is not traded for a type that weighs
more. And they are there in every session, because in our runs a good start
did not carry itself.

## The spring

Look at a mountain spring and you see at once why the water took exactly this
path. You do not have to study the soil grain by grain, because behind every
tiny "decision" the water made stood the same unyielding, constant force. Code
should read the same way: one glance, and you know why.

Only fools admire complexity. Beauty lies in simplicity and symmetry.
Complexity is chaos.
