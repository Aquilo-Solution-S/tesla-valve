import TeslaValve.Test.Refused.operation

/-- The light always stops traffic. -/
def orCatchAll : TrafficLight → Bool
  | .red | _ => true
