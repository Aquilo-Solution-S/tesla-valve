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

end TeslaValve.Test.Refused.unusedType
