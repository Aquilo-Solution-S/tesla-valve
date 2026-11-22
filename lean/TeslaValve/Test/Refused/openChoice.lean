/-- An amount: a case that carries a number, which no table can list. -/
inductive Amount where
  /-- So many. -/
  | of (n : Nat)
