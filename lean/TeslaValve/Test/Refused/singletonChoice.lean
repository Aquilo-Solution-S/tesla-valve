namespace TeslaValve.Test.Refused.singletonChoice

/-- The only case of a choice. -/
inductive Lone where
  | only

/-- A nested result with a single reason for refusal. -/
def outcomes : Bool → List (Except Lone Nat)
  | true => [.ok 1]
  | false => [.error .only]

/-- A shape with no fields. -/
structure Marker where

/-- The marker value. -/
def marker : Marker := {}

/-- The reason the count cannot be read. -/
inductive Admitted where
  | unavailable

/-- Read a count when it is available. -/
def admit : Bool → Except Admitted Nat
  | true => .ok 1
  | false => .error .unavailable

/-- A case wrapping a one-value choice. -/
inductive Wrapper where
  | wrap (reason : Admitted)

/-- A choice with no cases. -/
inductive Never where

/-- A purported error type that the decision never returns. -/
inductive UnusedError where
  | unavailable

/-- Return the count for each flag. -/
def alwaysSucceeds : Bool → Except UnusedError Nat
  | true => .ok 2
  | false => .ok 0

end TeslaValve.Test.Refused.singletonChoice
