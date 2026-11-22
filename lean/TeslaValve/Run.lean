import TeslaValve.View
open Lean

/-! What a project's own program calls: the check or the view of its ledger. -/

namespace TeslaValve

/-- Runs `check` or `view` for a project. Unsafe because it lets the imported extensions
initialize, which the class and instance checks read. -/
unsafe def run (config : Config) (args : List String) : IO UInt32 := do
  initSearchPath (← findSysroot)
  enableInitializersExecution
  match args with
  | ["check"] => check config
  | ["view"] => view config
  | _ =>
    IO.eprintln "error: usage: lake exe <program> check | view"
    return 2

end TeslaValve
