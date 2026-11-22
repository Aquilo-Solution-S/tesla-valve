import TeslaValve.Emit
open Lean

/-! What a project's own program calls: the check, the view, or what the ledger emits for the code. -/

namespace TeslaValve

/-- Runs `check`, `view`, `emit rust` or `emit vectors` for a project. Unsafe because it lets the imported extensions
initialize, which the class and instance checks read. -/
unsafe def run (config : Config) (args : List String) : IO UInt32 := do
  initSearchPath (← findSysroot)
  enableInitializersExecution
  match args with
  | ["check"] => check config
  | ["view"] => view config
  | ["emit", target] => emit config target
  | _ =>
    IO.eprintln "error: usage: lake exe <program> check | view | emit rust | emit vectors"
    return 2

end TeslaValve
