import TeslaValve.Test.Refused.operation

/-- Whether the light has constructor index one. -/
def ctorIdxLiteral (light : TrafficLight) : Bool :=
  match light with
  | .red => false
  | .amber | .green =>
    match TrafficLight.ctorIdx light with
    | 1 => true
    | _ => false
