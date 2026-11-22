instance : Inhabited Nat := ⟨1⟩

/-- A lamp. -/
inductive Lamp where
  /-- Lit. -/
  | on
  /-- Dark. -/
  | off

noncomputable instance : DecidableEq Lamp := fun a b => Classical.propDecidable (a = b)
