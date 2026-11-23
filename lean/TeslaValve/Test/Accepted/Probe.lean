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

/-- Whether an event allows a window. -/
def allowed : Event → Bool
  | .paint .red => true
  | .paint .blue | .toggle => false

/-- A window opened by an allowed event. -/
structure AllowedWindow where
  event : Event
  ok : allowed event = true

/-- The window red paint opens. -/
def redWindow : AllowedWindow := ⟨.paint .red, rfl⟩

/-- The text for each status. -/
def label : (state : State) → String
  | .«a b» => "x|y"
  | .aB => "other"

/-- The window for each status, built with `TeslaValve.Test.Accepted.Probe.Window.mk`. -/
def window : (_ : State) → Window
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
def applyEvent (currentStatus : State) (incomingEvent : Event) : Except PaintRefusal State :=
  match incomingEvent with
  | .toggle | .paint .red => .ok (advance currentStatus incomingEvent)
  | .paint .blue => .error .blueUnsupported

/-- The first natural number above the JavaScript exact integer range that needs rounding. -/
def wideNumber : Bool → Nat
  | true => 9007199254740993
  | false => 0

/-- Live, unforgotten content is visible. -/
def visibleInScope : (lifecycle : Bool) → (forgotten : Bool) → Bool
  | true, false => true
  | true, true | false, true | false, false => false

/-- Forgotten or inactive content is hidden. -/
def hiddenInScope : (lifecycle : Bool) → (forgotten : Bool) → Bool
  | true, false => false
  | true, true | false, true | false, false => true

/-- Retired, unforgotten content can be restored. -/
def restoreAdmission : (retired : Bool) → (forgotten : Bool) → Bool
  | true, false => true
  | true, true | false, true | false, false => false

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
