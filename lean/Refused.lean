/-! A ledger root must be audited even when a submodule imports it. -/

namespace Refused

/-- A claim with no proof in the root module. -/
axiom rootAxiom : False

end Refused
