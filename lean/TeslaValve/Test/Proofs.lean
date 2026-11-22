/-! Pure state in a proof library. -/

namespace TeslaValve.Test.Proofs

/-- Advance the state one step. -/
def stateful : EStateM String Nat Unit := modify (· + 1)

/-- The conditions on an incoming flag. -/
structure ValidFlag (ready : Bool) where
  count : Nat
  condition : Prop
  /-- The incoming flag is set. -/
  documented : ready = true
  bounded : ∀ n : Nat, n ≤ count → n ≤ count

/-- The flag is set by its documented premise. -/
theorem setByPremise (valid : ValidFlag ready) : ready = true := valid.documented

theorem sameProp (p q : Prop) (h : p ↔ q) : p = q := propext h

theorem sameQuot (r : Nat → Nat → Prop) (n m : Nat) (h : r n m) :
    Quot.mk r n = Quot.mk r m := Quot.sound h

theorem chosenProof (p : Prop) (h : Nonempty p) : p := Classical.choice h

end TeslaValve.Test.Proofs
