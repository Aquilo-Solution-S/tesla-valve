/-! A ledger with a constant of a type the Rust consumer defines. -/

namespace TeslaValve.Test.Accepted

/-- The colours. -/
inductive Colour where
  | red
  | blue

/-- The default colour. -/
def defaultColour : Colour := .blue

end TeslaValve.Test.Accepted
