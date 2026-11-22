/-- A decision over any type. -/
def same {α : Type} (a : α) : α := a

/-- A rule over any proposition, which says nothing of the ledger. -/
theorem vacuous {p : Prop} (h : p) : p := h
