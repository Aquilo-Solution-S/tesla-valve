/-- A shape with a signed number. -/
structure Offset where
  /-- Its distance, which may be below zero. -/
  distance : Int

/-- The readiness of a value. -/
inductive Readiness where
  | ready
  | waiting
  | unavailable

/-- Whether the value is ready. -/
def yes : Readiness → Bool
  | .ready => true
  | .waiting | .unavailable => false

/-- A shape with an invariant under the wrong field name. -/
structure RenamedProof where
  value : Readiness
  proofWithAnotherName : yes value = true

/-- A boolean constant. -/
def ready : Bool := true

/-- A shape whose invariant compares a constant. -/
structure ConstantProof where
  ok : ready = true
