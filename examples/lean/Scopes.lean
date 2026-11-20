import Audit

-- region: scopes
/-- The library of the spec, and which code holds which of its modules. A module
no scope lists is not tied to the code yet: the audit prints it, and no code
has to name what it declares. -/
def main : IO UInt32 := audit (library := `Spec) (scopes := [
  { spec := `Spec.Stock, code := ["../go"] },
  { spec := `Spec.Stock, code := ["../python/shop", "../python/tests"] },
  { spec := `Spec.Stock, code := ["../rust/src"] },
  { spec := `Spec.Stock, code := ["../typescript/src"] },
])
-- endregion
