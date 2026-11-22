import TeslaValve.Test.Refused.operation

/-- Whether the light is red, including when wrapped in an option. -/
def optionWildcard (light : TrafficLight) : Bool :=
  match light with
  | .red => true
  | .amber | .green =>
    match some light with
    | some .amber => true
    | _ => false
