import TeslaValve.Test.Refused.operation

/-- Whether an event toggles or paints red. -/
def payloadWildcard : PaintEvent → Bool
  | .toggle => true
  | .paint .red => true
  | .paint _ => false
