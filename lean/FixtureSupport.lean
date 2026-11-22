/-! Imported by fixtures and outside their configured libraries. -/

namespace FixtureSupport

abbrev Task₁ := IO
abbrev Task := Task₁
def task : Task Unit := pure ()

end FixtureSupport

namespace Refused.Foreign

def imported : Bool := true

end Refused.Foreign
