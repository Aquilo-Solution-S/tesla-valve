Run CI from this directory:

```sh
RUSTC_WRAPPER= cargo fmt --check
RUSTC_WRAPPER= cargo clippy --offline -- -D warnings
RUSTC_WRAPPER= cargo test --offline
```

Build: `RUSTC_WRAPPER= cargo build --release --offline`. The executable is `target/release/skirmish`.
