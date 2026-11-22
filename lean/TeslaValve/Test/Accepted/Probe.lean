import TeslaValve.Test.Accepted

/-! Decision outputs and full-name scope references. -/

namespace TeslaValve.Test.Accepted.Probe

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

/-- Whether a colour allows a window. -/
def allowed : Colour → Bool
  | .red => true
  | .blue => false

/-- A window whose flag passes the decision. -/
structure AllowedWindow where
  colour : Colour
  ok : allowed colour = true

/-- The text for each status. -/
def label : State → String
  | .«a b» => "x|y"
  | .aB => "other"

/-- The window for each status, built with `TeslaValve.Test.Accepted.Probe.Window.mk`. -/
def window : State → Window
  | .«a b» => ⟨2, true⟩
  | .aB => ⟨0, false⟩

/-- A description when the event carries a colour. -/
def description : Event → Option String
  | .toggle => none
  | .paint .red => some "red"
  | .paint .blue => some "blue"

/-- Whether the event carries paint. -/
def carriesPaint (event : Event) : Bool :=
  match event with
  | .toggle => false
  | .paint .red | .paint .blue =>
    match some event with
    | some (.paint .red) | some (.paint .blue) => true
    | some .toggle | none => false

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

/-- A list of available statuses. -/
def availableStates : List State := [.aB]

/-- The suggested status. -/
def suggestedState : Option State := some .aB

/-- An outcome with a choice of refusal. -/
def saved : Except State Nat := .ok 1

/-- The reason paint was refused. -/
inductive PaintRefusal where
  | blueUnsupported

/-- Apply an event, with blue paint refused. -/
def applyEvent (state : State) (event : Event) : Except PaintRefusal State :=
  match event with
  | .toggle | .paint .red => .ok (advance state event)
  | .paint .blue => .error .blueUnsupported

/-- The first natural number above the JavaScript exact integer range that needs rounding. -/
def wideNumber : Bool → Nat
  | true => 9007199254740993
  | false => 0

/-- Counts available to the Rust consumer. -/
def counts : List Nat := [2, 3]

/-- A count the Rust consumer can omit. -/
def maybeCount : Option Nat := some 2

/-- Counts with one missing entry. -/
def optionalCounts : List (Option Nat) := [none, some 2]

/-- Spelling with quotes, Markdown punctuation and control characters. -/
def exactText : String := "\"\\\n|_*\u202e\u0085"

/-- A shape with punctuation in a field label. -/
structure TextShape where
  «*flag*» : Bool

/-- A case with punctuation in its label. -/
inductive Label where
  | «a*b» (active : Bool)

end TeslaValve.Test.Accepted.Probe
