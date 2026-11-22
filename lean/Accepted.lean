/-! A ledger with a constant of a type the Rust consumer defines. -/

namespace Accepted

/-- The colours. -/
inductive Colour where
  | red
  | blue

/-- The default colour. -/
def defaultColour : Colour := .blue

end Accepted
