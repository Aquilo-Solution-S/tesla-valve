import TeslaValve.Test.Refused.operation

/-- Both lights are red. -/
def nestedWildcard (first second : TrafficLight) : Bool :=
  match first with
  | .red =>
    match second with
    | .red => true
    | _ => false
  | .amber | .green => false
