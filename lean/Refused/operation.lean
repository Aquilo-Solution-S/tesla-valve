/-- A light. -/
inductive Light where
  /-- Stop. -/
  | red
  /-- Go. -/
  | green
  deriving DecidableEq

/-- Whether to go, by an `if` in place of a match. -/
def go (light : Light) : Bool := if light = .green then true else false

/-- Whether a light is red. -/
def isRed : Light → Bool
  | .red => true
  | .green => false

/-- An alias of a decision. -/
def alias := isRed
