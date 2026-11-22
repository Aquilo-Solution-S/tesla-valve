import TeslaValve.Test.Refused.operation

/-- Red stops traffic. -/
def wildcard : Light → Bool
  | .red => true
  | _ => false
