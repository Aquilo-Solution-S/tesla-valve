/-- A rule the compiler vouches for instead of a proof. -/
theorem trusted : (1 : Nat) = 1 := by native_decide

/-- A bulb. -/
inductive Bulb where
  /-- Lit. -/
  | on
  | off
  | dim
  deriving DecidableEq

/-- Whether a bulb is lit. -/
def lit : Bulb → Bool
  | .on => true
  | .off | .dim => false

/-- A lit bulb. -/
structure Lit where
  /-- The bulb. -/
  light : Bulb
  /-- It is lit. -/
  ok : lit light = true

/-- A lit bulb whose invariant the compiler vouches for instead of a proof. -/
def shown : Lit := ⟨.on, by native_decide⟩

/-- A bulb whose deferred proof defaults to an assumption. -/
structure Deferred where
  light : Bulb
  ok : lit light = true := by sorry
