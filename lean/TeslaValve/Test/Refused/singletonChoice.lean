namespace TeslaValve.Test.Refused.singletonChoice

/-- The only case of a choice. -/
inductive Lone where
  | only

/-- A purported error type that the decision never returns. -/
inductive UnusedError where
  | unavailable

/-- Return the count for each flag. -/
def alwaysSucceeds : Bool → Except UnusedError Nat
  | true => .ok 2
  | false => .ok 0

end TeslaValve.Test.Refused.singletonChoice
