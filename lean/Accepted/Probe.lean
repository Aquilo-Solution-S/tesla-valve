import Accepted

/-! Decision outputs and full-name scope references. -/

namespace Accepted.Probe

/-- The two statuses. -/
inductive State where
  | «a b»
  | aB
  deriving
    DecidableEq

/-- An event that may carry a colour. -/
inductive Event where
  | toggle
  | paint (colour : Colour)

/-- A shape with a number and a flag. -/
structure Window where
  count : Nat
  active : Bool

/-- Whether a flag allows a window. -/
def allowed : Bool → Bool
  | true => true
  | false => false

/-- A window whose flag passes the decision. -/
structure AllowedWindow where
  active : Bool
  ok : allowed active = true

/-- The text for each status. -/
def label : State → String
  | .«a b» => "x|y"
  | .aB => "other"

/-- The window for each status. -/
def window : State → Window
  | .«a b» => ⟨2, true⟩
  | .aB => ⟨0, false⟩

/-- A description when the event carries a colour. -/
def description : Event → Option String
  | .toggle => none
  | .paint .red => some "red"
  | .paint .blue => some "blue"

/-- Paint or toggle the status. -/
def advance (state : State) (event : Event) : State :=
  match event with
  | .toggle => match state with
    | .«a b» => .aB
    | .aB => .«a b»
  | .paint .red => .«a b»
  | .paint .blue => .aB

/-- The largest Rust integer literal. -/
def _key : Nat := 340282366920938463463374607431768211455

/-- The named status. -/
def itemβ : State := .«a b»

/-- The status for a different consumer. -/
def notHeld : State := .aB

/-- A list of choices with no items. -/
def emptyStates : List State := []

/-- An optional choice with no value. -/
def absentState : Option State := none

/-- An outcome with a choice of refusal. -/
def saved : Except State Nat := .ok 1

end Accepted.Probe
