# Lean, as the spec language

Lean 4 holds the target where a type in the code cannot: a rule that more than
one codebase must keep, a protocol, a rule that is ahead of what is built. The
spec is a library of declarations the compiler checks, and the code is tied to
it by what it emits, replays or names. A rule that one type in one codebase
already holds needs no spec: that type is its home.

| what the rule is | declaration | enforcer |
| --- | --- | --- |
| a closed choice | `inductive` | the compiler: a match that misses a constructor does not build |
| a shape, and the invariant its constructor keeps | `structure`, or a subtype `{ x : T // p x }` | the compiler: no value exists without the proof |
| a decision | a total, computable `def` | the termination checker; the audit refuses `partial` and `noncomputable` |
| a rule | a proved `theorem` | the kernel; `--wfail` refuses `sorry`, and the audit refuses `axiom` |
| a protocol | `step : State → Event → Except Refusal State`, with the invariant preserved by every step and liveness as a property of the terminal states | the theorems over `step` |
| a rejected design | `theorem not_<alternative>`, which shows that the alternative breaks a rule | the kernel: the design cannot come back unnoticed |
| a worked example | `example`, `#guard` | the compiler evaluates it on every build |
| a word of the vocabulary | the type or constructor the model uses, defined by its docstring | the compiler: a name nothing declares does not resolve |

Prefer a shape that makes the wrong version unwritable, then a decision and a
theorem about it, then a protocol model: each step down is more to read and
more to keep proved.

## A decision, its rule and a rejected design

The docstring carries the why. `not_one_promise` keeps a design that was
turned down from returning: whoever makes every status promise the same date
has to delete a theorem to do it.

<!-- code: examples/lean/Spec/Stock.lean#stock -->
```lean
/-- What the warehouse says about an item. -/
inductive Stock where
  | inStock
  | backorder (restockDays : Nat)

/-- Days until the parcel arrives. -/
def deliveryDays (shipping : Nat) : Stock → Nat
  | .inStock => shipping
  | .backorder restockDays => restockDays + shipping

/-- A backorder never arrives before the same item in stock. -/
theorem backorder_not_sooner (shipping restockDays : Nat) :
    deliveryDays shipping .inStock ≤ deliveryDays shipping (.backorder restockDays) := by
  simp [deliveryDays]

/-- Rejected: one promise for every stock status. A backorder would be promised
the date of an item in stock. -/
theorem not_one_promise : ∃ shipping restockDays,
    deliveryDays shipping (.backorder restockDays) ≠ deliveryDays shipping .inStock :=
  ⟨0, 1, by decide⟩

#guard deliveryDays 2 (.backorder 3) == 5
```

## A protocol

Every step answers with the next state or the reason it is refused. The rule
is a theorem over `step`, and the last one is the liveness the model can
state: an order that can take no more steps holds no stock.

<!-- code: examples/lean/Spec/Reservation.lean#reservation -->
```lean
/-- An order and the stock it holds. -/
inductive Order where
  | placed (reserved : Nat)
  | shipped
  | cancelled
deriving DecidableEq

inductive Event where
  | ship
  | cancel

/-- Why a step is refused. -/
inductive Refusal where
  | alreadyShipped
  | alreadyCancelled
deriving DecidableEq

/-- Stock an order still holds back from other customers. -/
def reserved : Order → Nat
  | .placed n => n
  | .shipped | .cancelled => 0

def step : Order → Event → Except Refusal Order
  | .placed _, .ship => .ok .shipped
  | .placed _, .cancel => .ok .cancelled
  | .shipped, _ => .error .alreadyShipped
  | .cancelled, _ => .error .alreadyCancelled

/-- A reservation is released when the order is cancelled. -/
theorem cancel_releases (order next : Order) (h : step order .cancel = .ok next) :
    reserved next = 0 := by
  cases order <;> simp [step] at h <;> subst h <;> rfl

/-- No step ever holds back more stock than before. -/
theorem step_never_reserves_more (order next : Order) (event : Event)
    (h : step order event = .ok next) : reserved next ≤ reserved order := by
  cases order <;> cases event <;> simp [step] at h <;> subst h <;> simp [reserved]

/-- An order that can take no more steps holds no stock. -/
theorem terminal_holds_nothing (order : Order)
    (h : ∀ event, ∃ refusal, step order event = .error refusal) : reserved order = 0 := by
  cases order with
  | placed n => have ⟨_, h⟩ := h .ship; simp [step] at h
  | shipped => rfl
  | cancelled => rfl
```

## Not in the model

- `sorry`: a rule that is assumed is not held. `lake build --wfail` refuses
  it.
- `axiom`: an outside fact is a hypothesis of the theorem that needs it, so
  every reader sees what the rule rests on. The audit refuses it.
- `partial`, `unsafe`, `noncomputable`: a decision the code replays has to
  terminate and evaluate. The audit refuses them.
- `IO`: the model decides, and an emitter beside it writes files. The audit
  refuses it in the model.
- A library that slows the build: the spec builds in the gate on every
  change. A judgment call: Mathlib for one lemma adds minutes, and a gate
  that takes minutes is the step people skip.

The audit and the bad file that proves each refusal are in the prepare
skill's [Lean reference](../../prepare/references/lean.md).

## A prose record maps over

Its title becomes a name. Its rules become declarations. The why and the
hazards become the docstring. A "why not" becomes a `theorem not_…`, or stays
in the docstring where no theorem can state it. Its status, dates, names and
issue numbers go to git and the tracker.

## Every declaration has a consumer

A declaration nothing consumes is a gap or it is dead.

- **Emitted:** a shape generated into the code. The project's gate generates
  it again and fails when the file differs from the commit.
- **Replayed:** a decision evaluated on generated inputs into golden vectors,
  which a unit test of the code replays. The gate generates the vectors
  again, as it does an emitted shape.
- **Named:** the test that holds a rule carries the declaration's name, and a
  reader audits these. Only this one is manual, so it is the last resort.

The whole spec builds in the gate, not only what an emitter imports: the
library is the glob `Spec.+`, and a module nothing imports is still checked.
