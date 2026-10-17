# Driftfall

CI commands (run in this directory):

```sh
cargo fmt --check
cargo clippy --offline -- -D warnings
cargo test --offline
```

The game binary is built with `cargo build --release --offline` and runs as a JSON-lines
process.
