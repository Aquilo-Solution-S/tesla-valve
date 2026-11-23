import TeslaValve.Test.Refused.singletonChoice

namespace TeslaValve.Test.Refused.constantDecision

/-- The shared count. -/
def sharedCount : Nat := 2

/-- A decision whose alternatives compute the same count. -/
def repeatCount : Bool → Nat
  | true => sharedCount
  | false => 2

/-- A two-valued result that stays set for either input. -/
def alwaysSet : Bool → Bool
  | true => true
  | false => true

/-- A decision over a choice with only one value. -/
def overWrapper : singletonChoice.Wrapper → Nat
  | .wrap .unavailable => 1

end TeslaValve.Test.Refused.constantDecision
