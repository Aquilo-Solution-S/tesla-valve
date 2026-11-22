/-! An empty proof library can contain definitions and instances. -/

structure Box where
  count : Nat

instance boxExists : Nonempty Box := ⟨⟨0⟩⟩
