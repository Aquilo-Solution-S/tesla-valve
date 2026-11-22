namespace TeslaValve.Test.Refused.constantDecision

/-- The shared count. -/
def sharedCount : Nat := 2

/-- A decision whose alternatives compute the same count. -/
def repeatCount : Bool → Nat
  | true => sharedCount
  | false => 2

end TeslaValve.Test.Refused.constantDecision
