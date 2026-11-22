import TeslaValve
open Lean TeslaValve

def expect (holds : Bool) (message : String) : IO UInt32 := do
  if holds then return 0
  IO.eprintln s!"error: {message}"
  return 1

def includes (text fragment : String) : Bool :=
  (text.splitOn fragment).length > 1

/-- The outputs and scope scan of a ledger that passes the forms. -/
def accepted (place : String) : IO UInt32 := do
  let loaded ← Config.load { ledger := `Accepted }
  let refused ← refusals loaded
  let mut failed ← expect refused.isEmpty
    s!"Accepted: unexpected refusals {(refused.map fun r => s!"{r.name} {r.why.says}").toList}"
  let vectors ← emitVectors loaded
  let expected := Json.parse r#"{
    "Accepted.Probe.allowed": [
      {"in":[true],"out":true},
      {"in":[false],"out":false}
    ],
    "Accepted.Probe.label": [
      {"in":["a b"],"out":"x|y"},
      {"in":["aB"],"out":"other"}
    ],
    "Accepted.Probe.window": [
      {"in":["a b"],"out":{"count":2,"active":true}},
      {"in":["aB"],"out":{"count":0,"active":false}}
    ],
    "Accepted.Probe.description": [
      {"in":["toggle"],"out":null},
      {"in":[{"paint":["red"]}],"out":"red"},
      {"in":[{"paint":["blue"]}],"out":"blue"}
    ],
    "Accepted.Probe.advance": [
      {"in":["a b","toggle"],"out":"aB"},
      {"in":["a b",{"paint":["red"]}],"out":"a b"},
      {"in":["a b",{"paint":["blue"]}],"out":"aB"},
      {"in":["aB","toggle"],"out":"a b"},
      {"in":["aB",{"paint":["red"]}],"out":"a b"},
      {"in":["aB",{"paint":["blue"]}],"out":"aB"}
    ]
  }"#
  failed := failed + (← expect (expected.toOption == some vectors)
    s!"Accepted: unexpected vectors {vectors.compress}")
  let view ← viewModule loaded `Accepted.Probe
  for fragment in ["| «a b» | \"x\\|y\" | count: 2, active: yes |", "| aB | \"other\" | count: 0, active: no |",
      "| paint (blue) | \"blue\" |", "| toggle | — |", "state \"«a b»\" as s0", "state \"aB\" as s1",
      "s0 --> s1 : toggle", "s1 --> s0 : paint (red)"] do
    failed := failed + (← expect (includes view fragment) s!"Accepted: view omitted {fragment}")
  let unheld ← unheld loaded { rules := `Accepted.Probe, code := [place ++ "Accepted/Scope.txt"] }
  failed := failed + (← expect (unheld.any (·.name == `Accepted.Probe.notHeld))
    "Accepted: a longer name satisfied the scope")
  failed := failed + (← expect (!unheld.any (fun w => w.name ∈ [`Accepted.Probe._key, `Accepted.Probe.itemβ]))
    "Accepted: a quoted or Unicode name did not satisfy the scope")
  let rust ← emitRust { loaded with modules := #[`Accepted, `Accepted.Probe] }
  match rust with
  | .error why => failed := failed + (← expect false s!"Accepted: emit rust: {why}")
  | .ok text =>
    failed := failed + (← expect (includes text "(Accepted.Probe._key) =>" &&
      includes text "340282366920938463463374607431768211455")
      "Accepted: emit rust did not export the underscore name and maximum Nat")
    failed := failed + (← expect (!["defaultColour", "itemβ", "emptyStates", "absentState", "saved"].any (includes text))
      "Accepted: emit rust exported a type owned by the Rust consumer")
  let emptyRust ← emitRust { loaded with modules := #[`Accepted] }
  failed := failed + (← expect (emptyRust.toOption.any fun text =>
    includes text "macro_rules! ledger" && includes text "compile_error!" && !includes text "defaultColour")
    "Accepted: a choice-only ledger did not emit a usable macro")
  let tooLarge ← emitRust { loaded with modules := #[`Accepted.LargeNat] }
  failed := failed + (← expect (match tooLarge with
    | .error why => includes why "Accepted.LargeNat.tooLarge" && includes why "exceeds u128::MAX"
    | .ok _ => false) "Accepted: emit rust accepted a Nat larger than u128")
  return failed

/-- Each refusal is shown by its own module under `Refused/`, named as the refusal, which the
check refuses for that reason alone; and every module there shows one. -/
def selftest (place : String) : IO UInt32 := do
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
    if module != `Refused && !Refusal.all.any (`Refused ++ Name.mkSimple ·.name == module) then
      IO.eprintln s!"error: {module}: shows no refusal of the check"
      failed := failed + 1
  -- A file that links a name nothing declares: the dangling module, read as a file.
  let badLinks ← dangling loaded #[place ++ "Refused/dangling.lean"]
  for name in [`Refused.Nowhere.switch, `Refused.Foreign.imported, `Refused.Nowhere.nonexistentβ] do
    failed := failed + (← expect (badLinks.any (·.2 == name))
      s!"Refused/dangling.lean: {name}, read as a file, is not refused")
  -- A scan git cannot run fails, instead of finding no link.
  if (← (mentions loaded #[":(nonsense)x"]).toBaseIO) matches .ok _ then
    IO.eprintln "error: a git grep that fails is read as no links"
    failed := failed + 1
  -- The same modules as a proof library: a refusal that holds there still refuses its module,
  -- and one that does not refuses nothing there.
  let asProofs ← refusals { loaded with modules := #[], proofs := modules }
  for why in Refusal.all do
    let module := `Refused ++ Name.mkSimple why.name
    let here := asProofs.filter (·.module == module)
    if why.inProofs && !here.any (·.why == why) then
      IO.eprintln s!"error: {module}: as a proof library, the check does not refuse it as {why.name}"
      failed := failed + 1
    if !why.inProofs && here.any (·.why == why) then
      IO.eprintln s!"error: {module}: as a proof library, the check refuses it as {why.name}"
      failed := failed + 1
  for r in asProofs do
    if !r.why.inProofs then
      IO.eprintln s!"error: {r.module}: {r.name} is refused in a proof library as {r.why.name}, which holds only in the ledger"
      failed := failed + 1
  for (module, name, why) in [
      (`Refused, `Refused.rootAxiom, .isAxiom),
      (`Refused.doesIO, `concealed, .doesIO),
      (`Refused.doesIO, `Job, .doesIO),
      (`Refused.assumed, `Deferred, .assumed),
      (`Refused.dangling, `foreignLink, .dangling),
      (`Refused.dangling, `unicodeLink, .dangling),
      (`Refused.openShape, `RenamedProof, .openShape),
      (`Refused.openShape, `ConstantProof, .openShape),
      (`Refused.operation, `alias, .operation),
      (`Refused.openValue, `nested, .openValue)] do
    let inModule (r : Refused) := r.module == module && r.name == name && r.why == why
    failed := failed + (← expect (refused.any inModule) s!"{module}: {name} was not refused as {why.name}")
    if why.inProofs then
      failed := failed + (← expect (asProofs.any inModule) s!"{module}: {name} passed in a proof library")
  if failed == 0 then
    IO.println s!"Refused: each of the {Refusal.all.length} refusals is shown by its module, in the ledger and in a proof library"
    return 0
  return 1

/-- Unsafe because it lets the imported extensions initialize, which the class and instance
checks read. -/
unsafe def main : IO UInt32 := do
  initSearchPath (← findSysroot)
  let place ← placeInRepository
  enableInitializersExecution
  let refused ← selftest place
  enableInitializersExecution
  let accepted ← accepted place
  if accepted == 0 then
    IO.println "Accepted: vectors, view, Rust emission and full-name scopes passed"
  return refused + accepted
