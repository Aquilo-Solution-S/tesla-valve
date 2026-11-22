/-- A shape with a signed number. -/
structure Offset where
  /-- Its distance, which may be below zero. -/
  distance : Int

/-- Whether the value is ready. -/
def yes : Bool → Bool
  | true => true
  | false => false

/-- A shape with an invariant under the wrong field name. -/
structure RenamedProof where
  value : Bool
  proofWithAnotherName : yes value = true

/-- A boolean constant. -/
def ready : Bool := true

/-- A shape whose invariant compares a constant. -/
structure ConstantProof where
  ok : ready = true
