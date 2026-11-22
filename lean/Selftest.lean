import TeslaValve
open Lean TeslaValve

/-- Each refusal is shown by its own module under `Refused/`, named as the refusal, which the
check refuses for that reason alone; and every module there shows one. -/
def selftest : IO UInt32 := do
  let modules ← modulesOf `Refused
  let loaded ← load modules #[] [`Refused]
  let refused ← refusals loaded
  let mut failed := 0
  for why in Refusal.all do
    let module := `Refused ++ Name.mkSimple why.name
    if !modules.contains module then
      IO.eprintln s!"error: {why.name}: no module {module} shows it"
      failed := failed + 1
      continue
    let here := refused.filter (·.module == module)
    if here.isEmpty then
      IO.eprintln s!"error: {module}: the check does not refuse it"
      failed := failed + 1
    for r in here do
      if r.why != why then
        IO.eprintln s!"error: {module}: {r.name} is refused as {r.why.name}, not as {why.name}"
        failed := failed + 1
  for module in modules do
    if !Refusal.all.any (`Refused ++ Name.mkSimple ·.name == module) then
      IO.eprintln s!"error: {module}: shows no refusal of the check"
      failed := failed + 1
  -- A file that links a name nothing declares: the dangling module, read as a file.
  let place ← placeInRepository
  if (← dangling loaded.env loaded.roots #[place ++ "Refused/dangling.lean"]).isEmpty then
    IO.eprintln "error: Refused/dangling.lean: its link, read as a file, is not refused"
    failed := failed + 1
  -- A scan git cannot run fails, instead of finding no link.
  if (← (mentions [`Refused] #[":(nonsense)x"]).toBaseIO) matches .ok _ then
    IO.eprintln "error: a git grep that fails is read as no links"
    failed := failed + 1
  if failed == 0 then
    IO.println s!"Refused: each of the {Refusal.all.length} refusals is shown by its module"
    return 0
  return 1

/-- Unsafe because it lets the imported extensions initialize, which the class and instance
checks read. -/
unsafe def main : IO UInt32 := do
  initSearchPath (← findSysroot)
  enableInitializersExecution
  selftest
