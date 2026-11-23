namespace TeslaValve.Test.Refused.relabelDecision

/-- Return the input. -/
def forwardFlag : Bool → Bool
  | true => true
  | false => false

/-- Invert the input. -/
def invertFlag : Bool → Bool
  | true => false
  | false => true

/-- A change to a forgotten mark. -/
inductive MarkChange where
  | forget
  | restore

/-- Whether the mark is set after the change. -/
def markAfter : MarkChange → Bool
  | .forget => true
  | .restore => false

/-- An endpoint selection. -/
inductive Endpoint where
  | custom
  | default

/-- The endpoint selected by its flag. -/
def endpointChoice : (custom : Bool) → Endpoint
  | true => .custom
  | false => .default

/-- Where a service originates. -/
inductive Source where
  | core
  | spiice

/-- Whether a service is visible to everyone. -/
inductive Visibility where
  | «public»
  | «private»

/-- The visibility of each service source. -/
def serviceVisibility : Source → Visibility
  | .core => .«public»
  | .spiice => .«private»

/-- A choice whose two values come from its payload. -/
inductive WrappedFlag where
  | wrap (set : Bool)

/-- The wrapped flag with its value flipped. -/
def invertWrappedFlag : WrappedFlag → WrappedFlag
  | .wrap true => .wrap false
  | .wrap false => .wrap true

end TeslaValve.Test.Refused.relabelDecision
