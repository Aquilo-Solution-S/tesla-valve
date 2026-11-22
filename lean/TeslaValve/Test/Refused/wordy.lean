/-- A switch's position. It has one, and a second line that explains what the Lean
already says. -/
inductive Lever where
  /-- Down. -/
  | down
  | up
  deriving DecidableEq
