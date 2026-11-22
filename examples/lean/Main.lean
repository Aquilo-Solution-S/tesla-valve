-- region: config
import TeslaValve

unsafe def main (args : List String) : IO UInt32 :=
  TeslaValve.run {
    ledger := `Shop
    proofs := [`Spec]
    scopes := [
      { rules := `Spec.Stock, code := ["examples/go"] },
      { rules := `Spec.Stock, code := ["examples/python/shop", "examples/python/tests"] },
      { rules := `Spec.Stock, code := ["examples/rust/src"] },
      { rules := `Spec.Stock, code := ["examples/typescript/src"] },
      { rules := `Shop.Shipping, code := ["examples/rust/src"] },
    ]
    -- The tool has its own examples. The preparation guide quotes the broken links.
    unscanned := ["lean", "examples/bad/lean", "skills/prepare/references/lean.md"]
  } args
-- endregion
