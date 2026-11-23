/-! A ledger with a constant of a type the Rust consumer defines. -/

namespace TeslaValve.Test.Accepted

/-- The colours. -/
inductive Colour where
  | red
  | blue

/-- A choice whose single case carries two possible values. -/
inductive Flag where
  | flag (enabled : Bool)

/-- The default colour. -/
def defaultColour : Colour := .blue

end TeslaValve.Test.Accepted
