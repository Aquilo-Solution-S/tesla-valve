/-- A light. -/
inductive Light where
  /-- Stop. -/
  | red
  | amber
  /-- Go. -/
  | green
  deriving DecidableEq

/-- Whether to go, by an `if` in place of a match. -/
def go (light : Light) : Bool := if light = .green then true else false

/-- Whether a light is red. -/
def isRed : Light → Bool
  | .red => true
  | .amber | .green => false

/-- An alias of a decision. -/
def alias := isRed

/-- A light with three colours. -/
inductive TrafficLight where
  | red
  | amber
  | green

/-- An event that may carry a light setting. -/
inductive PaintEvent where
  | toggle
  | paint (light : Light)
