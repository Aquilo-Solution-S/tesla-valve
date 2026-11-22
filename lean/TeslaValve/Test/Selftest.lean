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
  let libraries := [`TeslaValve.Test.Proofs, `TeslaValve.Test.EmptyProofs, `TeslaValve.Test.MissingProofs]
  let loaded ← Config.load { ledger := `TeslaValve.Test.Accepted, proofs := libraries }
  let refused ← refusals loaded
  let mut failed ← expect refused.isEmpty
    s!"Accepted: unexpected refusals {(refused.map fun r => s!"{r.name} {r.why.says}").toList}"
  let inventory ← proofAxioms loaded loaded.proofs
  failed := failed + (← expect (emptyProofLibraries libraries inventory ==
    [`TeslaValve.Test.EmptyProofs, `TeslaValve.Test.MissingProofs])
    "Accepted: check did not distinguish empty proof libraries from a populated one")
  let report := proofReport inventory
  failed := failed + (← expect (report.splitOn "\n" == [
    "4 proof theorems (axiom-free: 1, propext: 1, Quot.sound: 1, Classical.choice: 1)",
    "TeslaValve.Test.Proofs.setByPremise: none",
    "TeslaValve.Test.Proofs.sameProp: propext",
    "TeslaValve.Test.Proofs.sameQuot: Quot.sound",
    "TeslaValve.Test.Proofs.chosenProof: Classical.choice"])
    s!"Accepted: unexpected axiom report {report}")
  let proofView ← viewProofs loaded `TeslaValve.Test.Proofs
  let emptyView ← viewProofs loaded `TeslaValve.Test.EmptyProofs
  failed := failed + (← expect (!includes emptyView "(axioms:")
    "Accepted: proof view counted an instance as a theorem")
  failed := failed + (← expect (match proofView.splitOn "✓ **set by premise** (axioms: none)" with
    | [before, after] => includes before "Premise **bounded**" && includes after "Premise **ordered**"
    | _ => false) "Accepted: proof view lost source order")
  for fragment in [
      "- Premise **documented**: The incoming flag is set.",
      "- Premise **bounded**: ∀ (n : Nat), n ≤ count → n ≤ count",
      "- Premise **ordered**: lo ≤ hi + lo",
      "✓ **same prop** (axioms: `propext`)",
      "✓ **same quot** (axioms: `Quot.sound`)",
      "✓ **chosen proof** (axioms: `Classical.choice`)"] do
    failed := failed + (← expect (includes proofView fragment) s!"Accepted: proof view omitted {fragment}")
  for field in ["documented", "bounded", "condition", "count"] do
    failed := failed + (← expect (!includes proofView s!"✓ **{field}**") s!"Accepted: view marked {field} proved")
  for field in ["condition", "count"] do
    failed := failed + (← expect (!includes proofView s!"Premise **{field}**") s!"Accepted: view treated {field} as a premise")
  let vectors ← emitVectors loaded
  let expected := Json.parse r#"{
    "TeslaValve.Test.Accepted.Probe.allowed": [
      {"in":["red"],"out":true},
      {"in":["blue"],"out":false}
    ],
    "TeslaValve.Test.Accepted.Probe.label": [
      {"in":["a b"],"out":"x|y"},
      {"in":["aB"],"out":"other"}
    ],
    "TeslaValve.Test.Accepted.Probe.window": [
      {"in":["a b"],"out":{"count":2,"active":true}},
      {"in":["aB"],"out":{"count":0,"active":false}}
    ],
    "TeslaValve.Test.Accepted.Probe.description": [
      {"in":["toggle"],"out":null},
      {"in":[{"paint":["red"]}],"out":"red"},
      {"in":[{"paint":["blue"]}],"out":"blue"}
    ],
    "TeslaValve.Test.Accepted.Probe.carriesPaint": [
      {"in":["toggle"],"out":false},
      {"in":[{"paint":["red"]}],"out":true},
      {"in":[{"paint":["blue"]}],"out":true}
    ],
    "TeslaValve.Test.Accepted.Probe.advance": [
      {"in":["a b","toggle"],"out":"aB"},
      {"in":["a b",{"paint":["red"]}],"out":"a b"},
      {"in":["a b",{"paint":["blue"]}],"out":"aB"},
      {"in":["aB","toggle"],"out":"a b"},
      {"in":["aB",{"paint":["red"]}],"out":"a b"},
      {"in":["aB",{"paint":["blue"]}],"out":"aB"}
    ],
    "TeslaValve.Test.Accepted.Probe.applyEvent": [
      {"in":["a b","toggle"],"out":{"ok":"aB"}},
      {"in":["a b",{"paint":["red"]}],"out":{"ok":"a b"}},
      {"in":["a b",{"paint":["blue"]}],"out":{"error":"blueUnsupported"}},
      {"in":["aB","toggle"],"out":{"ok":"a b"}},
      {"in":["aB",{"paint":["red"]}],"out":{"ok":"a b"}},
      {"in":["aB",{"paint":["blue"]}],"out":{"error":"blueUnsupported"}}
    ],
    "TeslaValve.Test.Accepted.Probe.wideNumber": [
      {"in":[true],"out":9007199254740993},
      {"in":[false],"out":0}
    ]
  }"#
  failed := failed + (← expect (expected.toOption == some vectors)
    s!"Accepted: unexpected vectors {vectors.compress}")
  let view ← viewModule loaded `TeslaValve.Test.Accepted.Probe
  for fragment in ["| «a b» | \"x\\|y\" | count: 2, active: yes |", "| aB | \"other\" | count: 0, active: no |",
      "| paint (blue) | \"blue\" |", "| toggle | — |", "state \"«a b»\" as s0", "state \"aB\" as s1",
      "s0 --> s1 : toggle", "s1 --> s0 : paint (red)",
      "| «a b» | paint (blue) | refused: blueUnsupported |", "| aB | paint (blue) | refused: blueUnsupported |",
      "**exact text** = ", "\\|\\_\\*", "- «a\\*b»", "- \\*flag\\*"] do
    failed := failed + (← expect (includes view fragment) s!"Accepted: view omitted {fragment}")
  let missing ← unheld loaded { rules := `TeslaValve.Test.Accepted.Probe, code := [place ++ "TeslaValve/Test/Accepted/Scope.txt"] }
  failed := failed + (← expect (missing.any (·.name == `TeslaValve.Test.Accepted.Probe.notHeld))
    "Accepted: a longer name satisfied the scope")
  failed := failed + (← expect (!missing.any (fun w => w.name ∈
    [`TeslaValve.Test.Accepted.Probe._key, `TeslaValve.Test.Accepted.Probe.itemβ,
      `TeslaValve.Test.Accepted.Probe.description]))
    "Accepted: a quoted or Unicode name did not satisfy the scope")
  failed := failed + (← expect (resolves loaded `TeslaValve.Test.Accepted.Probe._key)
    "Accepted: a written name with an underscore did not resolve")
  let generated ← unheld loaded {
    rules := `TeslaValve.Test.Accepted.Probe
    code := [place ++ "TeslaValve/Test/Accepted/ledger.rs"]
  }
  failed := failed + (← expect (generated.any (·.name == `TeslaValve.Test.Accepted.Probe._key))
    "Accepted: generated Rust held its exported declaration")
  for paths in [[], [":!other"], [":^other"], [":(top,exclude)other"], [":/^other"], [":"]] do
    let invalid ← (unheld loaded { rules := `TeslaValve.Test.Accepted.Probe, code := paths }).toBaseIO
    failed := failed + (← expect (match invalid with
      | .error why => includes why.toString "needs a positive code pathspec"
      | .ok _ => false) s!"Accepted: scope accepted {paths}")
  let rust ← emitRust { loaded with modules := #[`TeslaValve.Test.Accepted, `TeslaValve.Test.Accepted.Probe] }
  match rust with
  | .error why => failed := failed + (← expect false s!"Accepted: emit rust: {why}")
  | .ok text =>
    failed := failed + (← expect (includes text "(TeslaValve.Test.Accepted.Probe._key) =>" &&
      includes text "340282366920938463463374607431768211455")
      "Accepted: emit rust did not export the underscore name and maximum Nat")
    for fragment in ["[2, 3]", "Some(2)", "[None, Some(2)]", "\"\\\"\\\\\\n|_*\\u{202e}\\u{85}\""] do
      failed := failed + (← expect (includes text fragment) s!"Accepted: Rust omitted {fragment}")
    failed := failed + (← expect (!["defaultColour", "itemβ", "availableStates", "suggestedState", "saved"].any (includes text))
      "Accepted: emit rust exported a type owned by the Rust consumer")
  let emptyRust ← emitRust { loaded with modules := #[`TeslaValve.Test.Accepted] }
  failed := failed + (← expect (emptyRust.toOption.any fun text =>
    includes text "macro_rules! ledger" && includes text "compile_error!" && !includes text "defaultColour")
    "Accepted: a choice-only ledger did not emit a usable macro")
  let tooLarge ← emitRust { loaded with modules := #[`TeslaValve.Test.Accepted.LargeNat] }
  failed := failed + (← expect (match tooLarge with
    | .error why => includes why "TeslaValve.Test.Accepted.LargeNat.tooLarge" && includes why "exceeds u128::MAX"
    | .ok _ => false) "Accepted: emit rust accepted a Nat larger than u128")
  let nested ← emitRust { loaded with modules := #[`TeslaValve.Test.Accepted.NestedList] }
  failed := failed + (← expect (match nested with
    | .error why => includes why "NestedList.groups" && includes why "nested lists"
    | .ok _ => false) "Accepted: emit rust accepted a nested list")
  return failed

/-- Every refusal has a fixture module, and each fixture gets only its expected refusal. -/
def selftest (place : String) : IO UInt32 := do
  let root := `TeslaValve.Test.Refused
  let modules ← modulesOf root
  let loaded ← load modules #[] [root]
  let refused ← refusals loaded
  let asProofs ← refusals { loaded with modules := #[], proofs := modules }
  let mut failed := 0
  let fixture (why : Refusal) := root ++ Name.mkSimple why.name
  for why in Refusal.all do
    failed := failed + (← expect (modules.contains (fixture why))
      s!"{why.name}: no fixture module shows it")
  for module in modules do
    if module == root then continue
    let some why := Refusal.all.find? ((·.isPrefixOf module) ∘ fixture)
      | failed := failed + (← expect false s!"{module}: shows no refusal")
        continue
    let here := refused.filter (·.module == module)
    failed := failed + (← expect (!here.isEmpty && here.all (·.why == why))
      s!"{module}: expected only {why.name}, got {here.toList.map (·.why.name)}")
    let proofsHere := asProofs.filter (·.module == module)
    let proofWhy := if module == fixture .isInstance then .isNoncomputable else why
    let proofRefusal := proofWhy.inProofs && module != `TeslaValve.Test.Refused.isPartial.opaqueSort
    failed := failed + (← expect (proofsHere.isEmpty == !proofRefusal && proofsHere.all (·.why == proofWhy))
      s!"{module}: unexpected proof library refusals {proofsHere.toList.map (·.why.name)}")
  -- Lean adds an equality binder for a named pattern. Admit its module to isolate the matcher check.
  match loaded.written.find? (·.name == `namedPayload), moduleOf loaded.env ``Eq with
  | some named, some eqModule =>
    let withEquality := { loaded with modules := loaded.modules.push eqModule }
    let why ← withEquality.meta (refusal withEquality named)
    failed := failed + (← expect (why == some .operation) "namedPayload: accepted by the matcher check")
  | _, _ =>
    failed := failed + (← expect false "namedPayload: could not isolate the matcher check")
  -- A file that links a name nothing declares: the dangling module, read as a file.
  let badLinks ← dangling loaded #[place ++ "TeslaValve/Test/Refused/dangling.lean"]
  for name in [`TeslaValve.Test.Refused.Nowhere.switch, `TeslaValve.Test.Refused.Foreign.imported, `TeslaValve.Test.Refused.Nowhere.nonexistentβ] do
    failed := failed + (← expect (badLinks.any (·.2 == name))
      s!"TeslaValve/Test/Refused/dangling.lean: {name}, read as a file, is not refused")
  -- A scan git cannot run fails, instead of finding no link.
  if (← (mentions loaded #[":(nonsense)x"]).toBaseIO) matches .ok _ then
    IO.eprintln "error: a git grep that fails is read as no links"
    failed := failed + 1
  for name in [`TeslaValve.Test.Refused.isUp.match_1, `TeslaValve.Test.Refused.Switch.rec,
      `TeslaValve.Test.Refused.Switch.casesOn, `TeslaValve.Test.Refused.Switch.ctorIdx,
      `TeslaValve.Test.Refused.switchUp._proof_1] do
    failed := failed + (← expect (loaded.env.contains name && !resolves loaded name)
      s!"Refused: expected compiler-generated name {name} to be unresolvable")
  let stuck := `TeslaValve.Test.Refused.isPartial.opaqueValue
  let loadedStuck := { loaded with modules := #[stuck] }
  let markdown ← (viewModule loadedStuck stuck).toBaseIO
  let vectors ← (emitVectors loadedStuck).toBaseIO
  for (command, error) in [("view", markdown.map fun _ => ()), ("emit vectors", vectors.map fun _ => ())] do
    failed := failed + (← expect (match error with
      | .error why => includes why.toString "did not reduce to a list"
      | .ok _ => false) s!"Refused: {command} accepted a stuck list tail")
  for (module, name, why) in [
      (`TeslaValve.Test.Refused, `TeslaValve.Test.Refused.rootAxiom, .isAxiom),
      (`TeslaValve.Test.Refused.singletonChoice, `TeslaValve.Test.Refused.singletonChoice.Lone, .singletonChoice),
      (`TeslaValve.Test.Refused.singletonChoice, `TeslaValve.Test.Refused.singletonChoice.UnusedError, .singletonChoice),
      (`TeslaValve.Test.Refused.singletonChoice, `TeslaValve.Test.Refused.singletonChoice.Marker, .singletonChoice),
      (`TeslaValve.Test.Refused.singletonChoice, `TeslaValve.Test.Refused.singletonChoice.Wrapper, .singletonChoice),
      (`TeslaValve.Test.Refused.singletonChoice, `TeslaValve.Test.Refused.singletonChoice.Never, .singletonChoice),
      (`TeslaValve.Test.Refused.constantDecision, `TeslaValve.Test.Refused.constantDecision.overWrapper, .constantDecision),
      (`TeslaValve.Test.Refused.booleanDecision, `TeslaValve.Test.Refused.booleanDecision.forwardFlag, .booleanDecision),
      (`TeslaValve.Test.Refused.booleanDecision, `TeslaValve.Test.Refused.booleanDecision.invertFlag, .booleanDecision),
      (`TeslaValve.Test.Refused.emptyConstant, `TeslaValve.Test.Refused.emptyConstant.emptyFlags, .emptyConstant),
      (`TeslaValve.Test.Refused.emptyConstant, `TeslaValve.Test.Refused.emptyConstant.absentFlag, .emptyConstant),
      (`TeslaValve.Test.Refused.emptyConstant, `TeslaValve.Test.Refused.emptyConstant.moreEmptyFlags, .emptyConstant),
      (`TeslaValve.Test.Refused.doesIO, `concealed, .doesIO),
      (`TeslaValve.Test.Refused.doesIO, `Job, .doesIO),
      (`TeslaValve.Test.Refused.doesIO, `world, .doesIO),
      (`TeslaValve.Test.Refused.doesIO, `envelope, .doesIO),
      (`TeslaValve.Test.Refused.isAbbrev, `hiddenFlag, .isAbbrev),
      (`TeslaValve.Test.Refused.assumed, `Deferred, .assumed),
      (`TeslaValve.Test.Refused.dangling, `foreignLink, .dangling),
      (`TeslaValve.Test.Refused.dangling, `unicodeLink, .dangling),
      (`TeslaValve.Test.Refused.openShape, `RenamedProof, .openShape),
      (`TeslaValve.Test.Refused.openShape, `ConstantProof, .openShape),
      (`TeslaValve.Test.Refused.operation, `alias, .operation),
      (`TeslaValve.Test.Refused.openValue, `nested, .openValue)] do
    let inModule (r : Refused) := r.module == module && r.name == name && r.why == why
    failed := failed + (← expect (refused.any inModule) s!"{module}: {name} was not refused as {why.name}")
    if why.inProofs then
      failed := failed + (← expect (asProofs.any inModule) s!"{module}: {name} passed in a proof library")
  failed := failed + (← expect (!refused.any (·.name == `TeslaValve.Test.Refused.singletonChoice.Admitted))
    "Refused: a one-value choice used as a decision error was refused")
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
