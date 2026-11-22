/-! Imported by fixtures and outside their configured libraries. -/

namespace TeslaValve.Test.FixtureSupport

abbrev Task₁ := IO
abbrev Task := Task₁
def task : Task Unit := pure ()

structure ActionPacket where
  task : IO Unit

inductive Envelope where
  | packed : ActionPacket → Envelope

axiom outsideFact : False

end TeslaValve.Test.FixtureSupport

namespace TeslaValve.Test.Refused.Foreign

def imported : Bool := true

end TeslaValve.Test.Refused.Foreign
