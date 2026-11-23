/-! An empty proof library can contain definitions and instances. -/

structure Box where
  count : Nat

instance boxExists : Nonempty Box := ⟨⟨0⟩⟩

namespace Demo

scoped instance boxDefault : Inhabited Box := ⟨⟨0⟩⟩

end Demo
