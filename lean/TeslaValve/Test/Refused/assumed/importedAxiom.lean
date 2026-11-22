import TeslaValve.Test.FixtureSupport

/-- A rule that relies on the assumption in the imported module. -/
theorem importedAxiom : False := TeslaValve.Test.FixtureSupport.outsideFact
