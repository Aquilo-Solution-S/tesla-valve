# Lean

Put the ledger and its proof libraries in a Lake package beside the code.
[The Lean reference](../../tesla-valve/references/lean.md) explains the forms
and how the code holds the rules.

## The tools

Pin the toolchain in `lean-toolchain`. Elan uses that pin for commands run
under the package.

<!-- code: examples/lean/lean-toolchain -->
```text
leanprover/lean4:v4.35.0
```

Require the [teslavalve Lake package](../../../lean) and commit
`lake-manifest.json`. The example uses a path in the same repository. Use a
glob for each library so the build includes modules nothing imports.

<!-- code: examples/lean/lakefile.toml#libraries -->
```toml
[[require]]
name = "teslavalve"
path = "../../lean"

[[lean_lib]]
name = "Shop"
globs = ["Shop.+"]

[[lean_lib]]
name = "Spec"
globs = ["Spec.+"]
```

Give the project an executable that needs both libraries. It reads the
compiled modules when it runs.

<!-- code: examples/lean/lakefile.toml#shop -->
```toml
[[lean_exe]]
name = "shop"
root = "Main"
needs = ["Shop", "Spec"]
supportInterpreter = true
```

The program calls `TeslaValve.run` with the ledger, any proof libraries, and
the scopes. A scope's paths are relative to the Git root. Add the generated
Rust file as an exclusion. Use `unscanned` for the tool's own example links
and for the intentionally broken links in the fixtures and the guide that
quotes them.

<!-- code: examples/lean/Main.lean#config -->
```lean
unsafe def main (args : List String) : IO UInt32 :=
  TeslaValve.run {
    ledger := `Shop
    proofs := [`Spec]
    scopes := [
      { rules := `Spec.Stock, code := ["examples/go"] },
      { rules := `Spec.Stock, code := ["examples/python/shop", "examples/python/tests"] },
      { rules := `Spec.Stock, code := ["examples/rust/src", ":!examples/rust/src/ledger.rs"] },
      { rules := `Spec.Stock, code := ["examples/typescript/src"] },
      { rules := `Shop.Shipping, code := ["examples/rust/src", ":!examples/rust/src/ledger.rs"] },
    ]
    -- The tool has its own examples. The preparation guide quotes the broken links.
    unscanned := ["lean", "examples/bad/lean", "skills/prepare/references/lean.md"]
  } args
```

## The gate

Run the build and check from the project's Lean package. The compiler proves
the theorems and `--wfail` makes warnings fail the build. The check enforces
the forms, proof-library restrictions, docstrings, links and scopes.

```sh
lake build --wfail
lake exe shop check
```

Use `lake exe shop view` to read the ledger as Markdown, and
`lake exe shop emit vectors` to print the ledger decisions as JSON. Where the
code consumes generated Rust or vectors, regenerate them in the gate and
compare them with the commit. The shop writes its Nat-input vectors with its
own `vectors` program.

```sh
lake exe vectors
lake exe shop emit rust > ../rust/src/ledger.rs
git diff --exit-code HEAD
```

## The refusals

Run `lake build` and `lake test` in the tool's
[`lean/`](../../../lean) package. The selftest checks every
[`Refused/`](../../../lean/Refused) module for its own refusal. It checks
which restrictions also hold in a proof library.

Exercise the project's wiring in a separate Git checkout. Add the file to
the index where the gate can see it. A bad code file links a missing rule.

<!-- code: examples/bad/lean/stale.py -->
```python
# slot: ../python/tests/test_rush.py
# expect: links `Spec.rush_ships_today`, which neither the ledger nor a proof library declares
def test_a_rush_order_ships_today() -> None:
    """`Spec.rush_ships_today`"""
```

A bad Lean module belongs under a scoped module prefix. The shop puts this
one in `Spec/Stock/Unheld.lean`. It builds, and the check refuses it because
no code in a scope names its theorem.

<!-- code: examples/bad/lean/unnamed.lean -->
```lean
-- expect: Spec.in_stock_takes_shipping_only is named by no file under
import Spec.Stock

namespace Spec

/-- An item in stock takes the shipping time and no more. -/
theorem in_stock_takes_shipping_only (shipping : Nat) : deliveryDays shipping .inStock = shipping :=
  rfl

end Spec
```
