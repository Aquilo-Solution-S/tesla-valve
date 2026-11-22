import TeslaValve.Test.FixtureSupport

/-! A module whose docstrings link a ledger name that nothing declares. -/

/-- A switch's position, which `TeslaValve.Test.Refused.Nowhere.switch` decides. -/
inductive Position where
  /-- Up. -/
  | up
  | down
  deriving DecidableEq

/-- A link to an imported declaration `TeslaValve.Test.Refused.Foreign.imported`. -/
def foreignLink : Bool := true

/-- A link with a Unicode suffix `TeslaValve.Test.Refused.Nowhere.nonexistentβ`. -/
def unicodeLink : Bool := true

namespace TeslaValve.Test.Refused

/-- A switch position. -/
inductive Switch where
  | up
  | down

/-- Whether the switch is up. -/
def isUp : Switch → Bool
  | .up => true
  | .down => false

/-- A switch held in the up position. -/
structure UpSwitch where
  position : Switch
  ok : isUp position = true

/-- An upright switch with its proof. -/
def switchUp : UpSwitch := ⟨.up, by decide⟩

/-- Links to `TeslaValve.Test.Refused.isUp.match_1`, `TeslaValve.Test.Refused.Switch.rec` and `TeslaValve.Test.Refused.switchUp._proof_1`. -/
def internalLinks : Bool := true

end TeslaValve.Test.Refused
