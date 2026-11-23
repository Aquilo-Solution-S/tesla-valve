/-! An empty proof library can contain definitions and instances. -/

structure Box where
  count : Nat

instance boxExists : Nonempty Box := ⟨⟨0⟩⟩

namespace Demo

scoped instance boxDefault : Inhabited Box := ⟨⟨0⟩⟩

end Demo

@[instance_reducible] def outsideBox : Inhabited Box := ⟨⟨1⟩⟩

theorem outsideNonempty : Nonempty Box := ⟨⟨1⟩⟩

namespace Elsewhere

attribute [scoped instance] outsideBox outsideNonempty

end Elsewhere
