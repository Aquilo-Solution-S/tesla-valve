namespace TeslaValve.Test.Refused.idleInput

/-- A count that its second flag never changes. -/
def ignoresSecond : Bool → Bool → Nat
  | true, true => 1
  | true, false => 1
  | false, true => 0
  | false, false => 0

/-- A flag that its first input never changes. -/
def ignoresFirst : Bool → Bool → Bool
  | true, true => false
  | true, false => true
  | false, true => false
  | false, false => true

end TeslaValve.Test.Refused.idleInput
