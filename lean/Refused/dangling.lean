/-! A module whose docstrings link a ledger name that nothing declares. -/

/-- A switch's position, which `Refused.Nowhere.switch` decides. -/
inductive Position where
  /-- Up. -/
  | up
  deriving DecidableEq
