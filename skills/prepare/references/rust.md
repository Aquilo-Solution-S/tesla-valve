# Rust

| tool | holds | comes with |
| --- | --- | --- |
| rustc | every arm of a `match`, private fields, every field of a variant, a literal inside its type | the toolchain |
| clippy | no catch-all arm, no `unwrap` outside tests, no second `bool` parameter or field, no clock inside the logic | the toolchain, as the `clippy` component |
| doc tests | the one `compile_fail` line per shape | `cargo test`, for a library target |

## The tools

Pin the toolchain in `rust-toolchain.toml`: each release adds lints and changes
what they catch. `rustup toolchain install` reads the file, and every `cargo`
call below it uses that toolchain:

<!-- code: examples/rust/rust-toolchain.toml -->
```toml
[toolchain]
channel = "1.99.1"
components = ["clippy"]
```

Commit `Cargo.lock`, so `--locked` refuses a dependency that moved.

## The configs

In `Cargo.toml`. In a workspace, the table goes under
`[workspace.lints.clippy]` in the root, and each member takes it with
`lints.workspace = true`:

<!-- code: examples/rust/Cargo.toml#lints -->
```toml
[lints.clippy]
wildcard_enum_match_arm = "deny"
match_wildcard_for_single_variants = "deny"
unwrap_used = "deny"
expect_used = "deny"
fn_params_excessive_bools = "deny"
struct_excessive_bools = "deny"
disallowed_methods = "deny"
```

In `clippy.toml`, beside it. Name the clock of every time crate the project
uses:

<!-- code: examples/rust/clippy.toml -->
```toml
allow-unwrap-in-tests = true
allow-expect-in-tests = true
max-fn-params-bools = 1
max-struct-bools = 1
disallowed-methods = [
    { path = "chrono::Local::now", reason = "read the clock at the spring and pass it in" },
    { path = "chrono::Utc::now", reason = "read the clock at the spring and pass it in" },
    { path = "std::time::SystemTime::now", reason = "read the clock at the spring and pass it in" },
]
```

The clock ban finds every place the project reads the clock today. They move
behind one function, the way
[the clock](../../tesla-valve/references/rust.md#the-clock) shows.

## CI

```sh
rustup toolchain install
cargo clippy --all-targets --locked -- -D warnings
cargo test --locked
```

`--all-targets` lints the tests too, where `unwrap` stays allowed. `cargo test`
runs the doc tests, but only for a library. In a crate with only `main.rs`, or
where the project turns doc tests off, the compiler alone holds the shapes: it
gets no `lib.rs` and no doc tests turned on just for `compile_fail` lines.

## The proofs

Run `cargo clippy --all-targets -- -D warnings` in the copy. Rust compiles only
the files a module names, so the copy also gets `mod bad;` in `lib.rs`.

rustc refuses a missing arm, a backorder whose days are `None`, a literal out
of range and a forged value:

<!-- code: examples/bad/rust/missing_arm.rs -->
```rust
// expect: E0004
use crate::Stock;

pub fn restock_days(stock: Stock) -> u16 {
    match stock {
        Stock::Backorder { restock_days } => restock_days,
    }
}
```

<!-- code: examples/bad/rust/backorder_without_days.rs -->
```rust
// expect: E0308
use crate::Stock;

pub fn backorder() -> Stock {
    Stock::Backorder { restock_days: None }
}
```

<!-- code: examples/bad/rust/restock_days_out_of_range.rs -->
```rust
// expect: overflowing_literals
use crate::Stock;

pub fn backorder() -> Stock {
    Stock::Backorder { restock_days: 70000 }
}
```

<!-- code: examples/bad/rust/forged_postcode.rs -->
```rust
// expect: E0423
pub fn forged() -> crate::Postcode {
    crate::Postcode(String::from("hello"))
}
```

clippy refuses the rest:

<!-- code: examples/bad/rust/catch_all_arm.rs -->
```rust
// expect: match_wildcard_for_single_variants
use crate::Stock;

pub fn restock_days(stock: Stock) -> u16 {
    match stock {
        Stock::Backorder { restock_days } => restock_days,
        _ => 0,
    }
}
```

<!-- code: examples/bad/rust/unwrap_outside_tests.rs -->
```rust
// expect: unwrap_used
pub fn berlin() -> crate::Postcode {
    crate::Postcode::parse("10115").unwrap()
}
```

<!-- code: examples/bad/rust/two_bools.rs -->
```rust
// expect: fn_params_excessive_bools
pub fn ship(express: bool, gift: bool) -> u8 {
    u8::from(express) + u8::from(gift)
}
```

<!-- code: examples/bad/rust/bools_for_a_state.rs -->
```rust
// expect: struct_excessive_bools
pub struct Order {
    pub paid: bool,
    pub shipped: bool,
}
```

<!-- code: examples/bad/rust/clock_inside_logic.rs -->
```rust
// expect: disallowed_methods
pub fn today() -> chrono::NaiveDate {
    chrono::Utc::now().date_naive()
}
```
