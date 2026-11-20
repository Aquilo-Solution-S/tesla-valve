-- region: stock
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
-- endregion
