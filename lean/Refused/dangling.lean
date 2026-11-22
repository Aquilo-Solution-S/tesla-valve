import FixtureSupport

/-! A module whose docstrings link a ledger name that nothing declares. -/

/-- A switch's position, which `Refused.Nowhere.switch` decides. -/
inductive Position where
  /-- Up. -/
  | up
  deriving DecidableEq

/-- A link to an imported declaration `Refused.Foreign.imported`. -/
def foreignLink : Bool := true

/-- A link with a Unicode suffix `Refused.Nowhere.nonexistentβ`. -/
def unicodeLink : Bool := true
