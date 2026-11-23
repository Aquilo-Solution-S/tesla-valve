namespace TeslaValve.Test.Refused.unusedType

/-- Where a lamp hangs. -/
inductive Mount where
  | wall | ceiling
  deriving DecidableEq

/-- A lamp's mount and whether it is lit. -/
structure Placement where
  mount : Mount
  lit : Bool
  deriving DecidableEq

/-- How a lamp's shade is finished. -/
inductive Finish where
  | matte | gloss
  deriving DecidableEq

/-- A lamp's tint, compared only by the instance derived for it. -/
inductive Tint where
  | warm | cool

/-- A flag whose namespace holds that instance. -/
def Holder : Bool := true

namespace Holder

deriving instance DecidableEq for Tint

end Holder

end TeslaValve.Test.Refused.unusedType
