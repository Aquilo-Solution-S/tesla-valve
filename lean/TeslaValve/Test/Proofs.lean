import TeslaValve.Test.Accepted
import TeslaValve.Test.Accepted.Probe

/-! Pure state in a proof library. Its definitions, a shape's default and a proof are the
only uses of three ledger types. -/

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

/-- A bound whose default proof is computed by a tactic. -/
structure Ordered where
  lo : Nat
  hi : Nat
  ordered : lo ≤ hi + lo := by omega

theorem sameProp (p q : Prop) (h : p ↔ q) : p = q := propext h

theorem sameQuot (r : Nat → Nat → Prop) (n m : Nat) (h : r n m) :
    Quot.mk r n = Quot.mk r m := Quot.sound h

theorem chosenProof (p : Prop) (h : Nonempty p) : p := Classical.choice h

def underOne (n : Nat) (_h : n < 1) : Nat := n

def «back`tick» : Nat := 1

def ticked (n : Fin («back`tick» + 1)) : Nat := n.val

/-- A new lamp's flag is off. -/
def startsOff : Bool := match TeslaValve.Test.Accepted.Flag.flag false with
  | .flag enabled => !enabled

/-- A shade whose punctuated flag starts set. -/
structure Shaded where
  set : Bool := (⟨true⟩ : TeslaValve.Test.Accepted.Probe.TextShape).«*flag*»

theorem labelled : True := (fun (_ : TeslaValve.Test.Accepted.Probe.Label) => trivial) (.«a*b» true)

private theorem quiet : True := trivial

end TeslaValve.Test.Proofs
