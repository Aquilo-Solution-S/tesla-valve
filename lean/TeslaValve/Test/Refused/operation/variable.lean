import TeslaValve.Test.Refused.operation

/-- Red becomes amber. -/
def variableCatchAll : TrafficLight → TrafficLight
  | .red => .amber
  | other => other
