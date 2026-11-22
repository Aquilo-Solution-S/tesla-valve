import FixtureSupport

/-- A greeting that prints instead of answering. -/
def greet : IO Unit := IO.println "hello"

/-- An action whose IO type comes from an imported alias. -/
def concealed : FixtureSupport.Task Unit := FixtureSupport.task

/-- An action held as a field. -/
structure Job where
  task : IO Unit
