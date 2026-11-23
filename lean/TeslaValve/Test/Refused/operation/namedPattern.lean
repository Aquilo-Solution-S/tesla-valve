import TeslaValve.Test.Refused.operation

/-- Whether an event paints red. -/
def namedPayload : PaintEvent → Bool
  | .toggle | .paint .amber | .paint .green => false
  | .paint (light@.red) => isRed light
