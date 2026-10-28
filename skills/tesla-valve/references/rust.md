# Rust

Rust is bedrock: its guarantees still hold while the code runs, and stepping
outside them takes a word everyone can see, such as `unsafe`. Lean on the
compiler, and let clippy refuse what the compiler allows.

| wrong shape | right shape | enforcer | not when |
| --- | --- | --- | --- |
| a closed choice as `String` or `&str`, compared to literals | an enum, matched without `_` | the compiler's exhaustiveness check; `wildcard_enum_match_arm` and `match_wildcard_for_single_variants` | the set is owned elsewhere and can grow: parse it at the spring, and refuse or keep an explicit unknown |
| an `Option` that must be `Some` in one state | a variant that carries its data | the compiler: the field takes no `None`; a `compile_fail` doc test | the value is optional in every state |
| several `bool` fields that together encode one state: `paid`, `shipped`, `cancelled` | an enum of the states, each carrying its data | `struct_excessive_bools` with `max-struct-bools = 1` | the bools are truly independent: `#[expect(clippy::struct_excessive_bools, reason = "...")]` says why |
| a count wider than its range, so a sum can overflow | the narrowest integer that holds the range | serde refuses a value out of range; a literal out of range does not compile; a `compile_fail` doc test | never |
| a public field on a value with an invariant | a private field, one constructor returning `Result<Self, Invalid>` | privacy; one `compile_fail` doc test that tries to forge one | a value with no invariant stays a primitive |
| `#[derive(Deserialize)]` on a value with an invariant | deserialize through the constructor | a spring test that feeds it bad data: the derive never calls `parse` | the value has no invariant beyond its shape |
| a permit checked beside the call it authorizes | the permit contains the call, entry takes it by value, no `Clone` or `Copy` | `compile_fail` doc tests for reuse and for clone | the halves come from two systems and can disagree: keep a typed result |
| `fn f(express: bool, gift: bool)` | an enum whose variants name the choice | `fn_params_excessive_bools` with `max-fn-params-bools = 1` | one `bool` that is truly two-valued and named by its parameter |
| `.unwrap()` or `.expect()` on data from outside | a parse that returns a typed error | `unwrap_used` and `expect_used`, allowed in tests | a value the types already proved: `#[expect(clippy::unwrap_used, reason = "...")]` says why |
| a loose struct deserialized, then checked field by field | deserialize straight into the domain type | serde: the derive is the check | the wire format differs from the domain: a wire type, then `TryFrom` |
| `let _ = reserve(..)`, or `.ok()` on the answer of a commit | handle the refusal or pass it on with `?`; `#[must_use = "..."]` on a permit or a step that must be finished | `let_underscore_must_use` and `unused_result_ok`; rustc's `unused_must_use` for a bare call | never |
| callers comparing the text of a refusal, or `Result<_, ()>` | an enum of the reasons, matched without `_` | exhaustiveness; `result_unit_err` | callers only show the reason: one message is enough |
| the clock read deep inside the logic | read it at the spring and pass the date in | `disallowed_methods` | the one function that reads it, under `#[expect(clippy::disallowed_methods, reason = "...")]` |
| a count narrowed with `as`: `raw as u16` | `u16::try_from(raw)` at the spring; `u64::from(days)` to widen | `as_conversions`, `cast_possible_truncation` and `cast_sign_loss` | a float conversion no `From` covers: `#[expect(clippy::as_conversions, reason = "...")]` says why |
| `unsafe` in a crate that needs none, so a `transmute` forges a `Postcode` | no `unsafe`; a way past the constructor is an `unsafe fn` named `..._unchecked`, or nothing | `unsafe_code = "forbid"` under `[lints.rust]` | FFI or a measured need: `unsafe` stays, and `undocumented_unsafe_blocks` asks each block why |
| `#[allow(clippy::...)]`, or an `#[expect]` that does not say why | `#[expect(lint, reason = "...")]` on the narrowest item | `allow_attributes` and `allow_attributes_without_reason`; an `#[expect]` whose lint stops firing warns | code a macro or a generator writes |

## A closed choice, parsed at the spring

The derive is the check: an unknown status is refused with "unknown variant",
a backorder without its days with "missing field `restock_days`", and a count
out of range with "expected u16". The `match` has no `_`, so a new variant
stops the build at every match that has not decided what it means.

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

`restock_days` is a `u16`, so the sum cannot overflow. A `u64` from the
warehouse could, and a release build would wrap it silently into a wrong date.

Two `compile_fail` lines hold the shape, beside one that compiles:

<!-- code: examples/rust/src/lib.rs#stock-proofs -->
````rust
/// A backorder carries its restock days, and they fit in a `u16`:
///
/// ```
/// shop::Stock::Backorder { restock_days: 5 };
/// ```
///
/// ```compile_fail
/// shop::Stock::Backorder { restock_days: None };
/// ```
///
/// ```compile_fail
/// shop::Stock::Backorder { restock_days: 70000 };
/// ```
````

Each starts compiling the day its shape loosens: `None` once the field is an
`Option` again, `70000` once it is wider than a `u16`. `Backorder {}` would
prove neither, because a missing field fails to compile either way.

Cargo runs doc tests only for a library, and only where the project leaves them
on. In a crate with only `main.rs`, or where the project turns doc tests off,
the compiler alone holds these shapes: write no test that runs `rustc`,
trybuild included, and split no crate to get one.

## One constructor, held by a doc test

The second doc test fails the day someone makes the field public, the third
the day someone gives it a `Default`, the fourth the day a `From<String>` lets
any string in. Keep each body to the one line, because a `compile_fail` test
passes on any error, and stable Rust does not check the error code. The first
doc test compiles the same path, so a misspelled crate name cannot make the
second one pass.

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

When a `Postcode` arrives as JSON, `#[derive(Deserialize)]` would fill the
field without calling `parse`, and `"hello"` would become a postcode.
Deserialize through the constructor instead, by hand or with
`#[serde(try_from = "String")]`:

<!-- code: examples/rust/src/postcode.rs#deserialize -->
```rust
impl<'de> Deserialize<'de> for Postcode {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let raw = String::deserialize(deserializer)?;
        Postcode::parse(&raw).map_err(|Invalid(reason)| serde::de::Error::custom(reason))
    }
}
```

Privacy guards the field from other modules, not from the type's own. In it,
a derived `Default` makes an empty postcode, a `From<String>` turns any string
into one, and `DerefMut`, `AsMut<String>` or a `_mut` accessor changes one
after `parse` passed it. The compiler accepts each of them. Keep the module
small, give the type no `Default`, convert from the raw type only through
`TryFrom` or `FromStr` that call `parse`, and hand out `&str`, never
`&mut String`. `fallible_impl_from` refuses a `From` that panics or unwraps,
though not one that calls `.expect()`; nothing refuses a `From` that cannot
fail, which is why the doc tests above hold it.

## The clock

`disallowed_methods` refuses the clock everywhere but in the one function that
reads it, which says why it may. `#[expect]` fails the build if the lint ever
stops firing there:

<!-- code: examples/rust/src/lib.rs#clock -->
```rust
/// The clock is a spring: read it here, once, and pass the date in.
#[expect(clippy::disallowed_methods, reason = "the one place that reads the clock")]
pub fn today() -> NaiveDate {
    chrono::Local::now().date_naive()
}
```

The
[Rust example](https://github.com/Aquilo-Solution-S/tesla-valve/tree/main/examples/rust)
runs every enforcer above, and each is fed a file it must refuse.
