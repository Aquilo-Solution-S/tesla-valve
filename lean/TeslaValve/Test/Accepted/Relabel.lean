namespace TeslaValve.Test.Accepted.Relabel

/-- The available colours. -/
inductive Colour where
  | red
  | blue
  | green

/-- The colour selected by an alert flag. -/
def alertColour : Bool → Colour
  | true => .red
  | false => .blue

/-- The alert could not be cleared. -/
inductive ClearError where
  | alertActive

/-- Clear the flag only when no alert is active. -/
def clearAlert : Bool → Except ClearError Bool
  | true => .error .alertActive
  | false => .ok false

end TeslaValve.Test.Accepted.Relabel
