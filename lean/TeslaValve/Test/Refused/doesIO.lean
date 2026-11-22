import TeslaValve.Test.FixtureSupport

/-- A greeting that prints instead of answering. -/
def greet : IO Unit := IO.println "hello"

/-- An action whose IO type comes from an imported alias. -/
def concealed : TeslaValve.Test.FixtureSupport.Task Unit := TeslaValve.Test.FixtureSupport.task

/-- An action held as a field. -/
structure Job where
  task : IO Unit

/-- An optional outside world. -/
def world : Option IO.RealWorld := none

/-- A computation hidden in an imported inductive and structure. -/
def envelope : Option TeslaValve.Test.FixtureSupport.Envelope := none
