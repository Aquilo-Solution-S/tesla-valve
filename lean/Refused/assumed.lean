/-- A rule the compiler vouches for instead of a proof. -/
theorem trusted : (1 : Nat) = 1 := by native_decide

/-- A bulb. -/
inductive Bulb where
  /-- Lit. -/
  | on
  deriving DecidableEq

/-- Whether a bulb is lit. -/
def lit : Bulb → Bool
  | .on => true

/-- A lit bulb. -/
structure Lit where
  /-- The bulb. -/
  light : Bulb
  /-- It is lit. -/
  ok : lit light = true

/-- A lit bulb whose invariant the compiler vouches for instead of a proof. -/
def shown : Lit := ⟨.on, by native_decide⟩
