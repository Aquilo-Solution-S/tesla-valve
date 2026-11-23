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

/-- How dark a shade is. -/
inductive Shade where
  | dark | pale

/-- A count that starts at zero. -/
structure Counted where
  count : Nat := 0

/-- A count whose start an inherited field's default takes from a shade. -/
structure Shaded extends Counted where
  count := (fun (_ : Shade) => 1) .dark

end TeslaValve.Test.Refused.unusedType
