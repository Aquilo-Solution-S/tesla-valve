/-! Pure state in a proof library. -/

namespace TeslaValve.Test.Proofs

/-- Advance the state one step. -/
def stateful : EStateM String Nat Unit := modify (· + 1)

end TeslaValve.Test.Proofs
