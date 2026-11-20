-- slot: Spec/Rush.lean
-- expect: its modules do not load as one model
/-- A second decision of the same name, in a module that does not import the first. -/
def deliveryDays (shipping : Nat) : Nat := shipping
