-- expect: someDays is noncomputable
noncomputable def someDays : Nat := Classical.choice ⟨0⟩
