namespace TeslaValve.Test.Refused.booleanDecision

/-- Return the input. -/
def forwardFlag : Bool → Bool
  | true => true
  | false => false

/-- Invert the input. -/
def invertFlag : Bool → Bool
  | true => false
  | false => true

end TeslaValve.Test.Refused.booleanDecision
