-- region: reservation
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
-- endregion
