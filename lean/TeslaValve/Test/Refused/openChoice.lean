/-- An amount: a case that carries a number, which no table can list. -/
inductive Amount where
  /-- So many. -/
  | of (n : Nat)

/-- A switch's position, as a proposition, whose cases a decision cannot tell apart. -/
inductive Stance : Prop where
  /-- Up. -/
  | up
  /-- Down. -/
  | down
