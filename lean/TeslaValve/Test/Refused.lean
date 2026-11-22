/-! A ledger root must be audited even when a submodule imports it. -/

namespace TeslaValve.Test.Refused

/-- A claim with no proof in the root module. -/
axiom rootAxiom : False

end TeslaValve.Test.Refused
