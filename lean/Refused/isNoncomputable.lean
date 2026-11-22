/-- A value that does not evaluate. -/
noncomputable def chosen : Nat := Classical.choice ⟨1⟩
