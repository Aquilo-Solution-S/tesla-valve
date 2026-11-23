import TeslaValve.Forms
open Lean

/-! The view of the ledger, drawn by evaluation: each choice with its cases, each
decision as a table of every input, each state machine as a state diagram, and each rule
beside them. Nothing of it is drawn by hand, so it cannot disagree with the ledger. -/

namespace TeslaValve

/-- A name in words: `allItsPersonReads` and `all_its_person_reads` read "all its person reads". -/
def words (name : Name) : String := Id.run do
  let text := match name with
    | .str _ last => last
    | _ => name.toString
  let mut out := ""
  for c in text.toList do
    if c == '_' then out := out.push ' '
    else if c.isUpper then out := (if out.isEmpty then out else out.push ' ').push c.toLower
    else out := out.push c
  return out

/-- The constructor's spelling distinguishes cases whose names read the same in words. -/
def caseLabel (name : Name) : String :=
  match name with
  | .str _ last => (Name.mkSimple last).toString
  | _ => name.toString

/-- A type's name in words, capitalized: `Reader` reads "Reader". -/
def title (name : Name) : String :=
  let w := words name
  (w.take 1).toString.toUpper ++ (w.drop 1).toString

/-- A docstring on one line. -/
def oneLine (doc : String) : String :=
  " ".intercalate ((doc.splitOn "\n").map (·.trimAscii.toString) |>.filter (!·.isEmpty))

/-- Text as a Markdown code span, delimited by more backticks than its longest run. -/
def codeSpan (text : String) : String := Id.run do
  let mut longest := 0
  let mut run := 0
  for c in text.toList do
    run := if c == '`' then run + 1 else 0
    longest := max longest run
  let fence := String.ofList (List.replicate (longest + 1) '`')
  let pad := if text.startsWith "`" || text.endsWith "`" then " " else ""
  return fence ++ pad ++ text ++ pad ++ fence

/-- The docstring of a declaration, on one line. -/
def docOf (env : Environment) (name : Name) : IO String := do
  return oneLine ((← findDocString? env name).getD "")

/-- A label, and after it the docstring where there is one. -/
def captioned (label doc : String) : String :=
  if doc.isEmpty then label else s!"{label}: {doc}"

/-- The types of a constructor's fields, after its parameters. -/
def fieldTypes (type : Expr) (params : Nat) : List Expr :=
  match type, params with
  | .forallE _ _ body _, n + 1 => fieldTypes body n
  | .forallE _ field body _, 0 => field.consumeTypeAnnotations :: fieldTypes body 0
  | _, _ => []

/-- A shape's named values, omitting its invariant proof. -/
def shapeFields (env : Environment) (info : ConstructorVal) (fields : Array Expr) : List (Name × Expr) :=
  let names := getStructureFields env info.induct
  ((names.toList.zip fields.toList).zip (fieldTypes info.type info.numParams)).filterMap
    fun (field, type) => if type.isAppOf ``Eq then none else some field

/-- The items of a list the ledger computed, in order. -/
partial def listItems (e : Expr) : Except String (List Expr) :=
  match e.getAppFn, e.getAppArgs with
  | .const ``List.nil _, #[_] => .ok []
  | .const ``List.cons _, #[_, head, tail] => (listItems tail).map (head :: ·)
  | _, _ => .error s!"{e} did not reduce to a list"

/-- A value the ledger computed, in words. A shape shows its fields without its proof. -/
partial def render (env : Environment) (e : Expr) : Except String String := do
  let args := e.getAppArgs
  match e.getAppFn with
  | .const ``Option.none _ => return "—"
  | .const ``Option.some _ | .const ``Except.ok _ => render env args.back!
  | .const ``Except.error _ => return s!"refused: {← render env args.back!}"
  | .const ``Bool.true _ => return "yes"
  | .const ``Bool.false _ => return "no"
  | .const ``OfNat.ofNat _ => render env args[1]!
  | .lit (.natVal n) => return toString n
  | .lit (.strVal s) => return s.quote
  | .const ``List.nil _ | .const ``List.cons _ =>
    return s!"[{", ".intercalate (← (← listItems e).mapM (render env))}]"
  | .const ctor _ => match env.find? ctor with
    | some (.ctorInfo info) =>
      let fields := args.extract info.numParams args.size
      if isStructure env info.induct then
        return ", ".intercalate (← (shapeFields env info fields).mapM fun (field, v) =>
          return s!"{words field}: {← render env v}")
      else if fields.isEmpty then return caseLabel ctor
      else return s!"{caseLabel ctor} ({", ".intercalate (← fields.toList.mapM (render env))})"
    | _ => throw s!"{e} did not reduce to a ledger value"
  | _ => throw s!"{e} did not reduce to a ledger value"

/-- Gives a failed value conversion the name of the declaration that produced it. -/
def computed (name : Name) (answer : Except String α) : IO α :=
  match answer with
  | .ok value => pure value
  | .error why => throw <| IO.userError s!"{name}: {why}"

/-- What a decision answers for each of its inputs. -/
def evaluate (loaded : Loaded) (decision : Name) (inputs : List Expr) : IO String := do
  let answer ← loaded.reduce decision inputs.toArray
  computed decision (render loaded.env answer)

/-- Escape a value or label for Markdown prose or a table cell. -/
def escape (text : String) : String :=
  text.replace "\\" "\\\\" |>.replace "|" "\\|" |>.replace "`" "\\`" |>.replace "*" "\\*"
    |>.replace "_" "\\_" |>.replace "[" "\\[" |>.replace "<" "\\<" |>.replace "&" "\\&"
    |>.replace ">" "\\>" |>.replace "#" "\\#" |>.replace "~" "\\~"
    |>.replace "\r" "" |>.replace "\n" "<br>"

/-- A case or a field as a list item. -/
def item (env : Environment) (label : String) (name : Name) : IO String := do
  return "- " ++ captioned (escape label) (← docOf env name)

/-- A table with a header row. -/
def table (header : List String) (rows : List (List String)) : String :=
  let line (cells : List String) := "| " ++ " | ".intercalate (cells.map escape) ++ " |"
  "\n".intercalate ([line header, line (header.map fun _ => "---")] ++ rows.map line)

/-- The name of a type, in words. -/
def typeWords (type : Expr) : String :=
  match type.getAppFn with
  | .const name _ => words name
  | _ => toString type

/-- Plain arrows and wildcard binders carry generated names in Lean. -/
private def writtenBinder (name : Name) : Option Name :=
  if name.isAnonymous || name.hasMacroScopes || name.isInaccessibleUserName then none else some name

/-- The input column uses its written name, or its type name for a plain arrow or wildcard. -/
private def inputHeader (type : Expr) (binder : Name) : String :=
  ((writtenBinder binder).map words).getD (typeWords type)

/-- Whether a decision is a state machine: `State → Event → State`, or inside `Except`. An
event is its own choice, so `A → A → A` joins two values and is drawn as a table. -/
def machine? (type : Expr) : Option (Expr × Expr) :=
  match arrows type with
  | (#[state, event], .app (.app (.const ``Except _) _) next)
  | (#[state, event], next) => if next == state && event != state then some (state, event) else none
  | _ => none

/-- Mermaid's entity notation keeps punctuation inside a diagram label. -/
def diagramLabel (s : String) : String :=
  s.replace "#" "#35;" |>.replace "\"" "#34;" |>.replace "`" "#96;"
    |>.replace "%" "#37;" |>.replace "<" "#60;" |>.replace ">" "#62;"
    |>.replace "&" "#38;" |>.replace "\r" "#13;" |>.replace "\n" "#10;"

/-- The view of one module. -/
def viewModule (loaded : Loaded) (module : Name) : IO String := do
  let env := loaded.env
  let mut out := #[]
  let doc := (getModuleDoc? env module).map (·.toList.map (·.doc)) |>.getD []
  for d in doc do
    out := out.push ("\n".intercalate ((d.trimAscii.toString.splitOn "\n").map fun l => if l.startsWith "#" then "#" ++ l else l))
  if doc.isEmpty then out := out.push s!"## {escape module.toString}"
  -- A case or a field is drawn with its type, not on its own.
  let here := loaded.written.filter fun w =>
    w.module == module && w.standsAlone env
  -- The choices and shapes, with their cases and fields.
  for w in here do
    let .inductInfo type := w.info | continue
    let mut block := #[captioned s!"**{escape (title w.name)}**" (← docOf env w.name), ""]
    if isStructure env w.name then
      for field in getStructureFields env w.name do
        block := block.push (← item env (words field) (w.name ++ field))
    else
      for ctor in type.ctors do
        block := block.push (← item env (caseLabel ctor) ctor)
    out := out.push ("\n".intercalate block.toList)
  -- The constants.
  for w in here do
    let .defnInfo d := w.info | continue
    if !(arrows d.type).1.isEmpty then continue
    out := out.push (captioned s!"**{escape (words w.name)}** = {escape (← evaluate loaded w.name [])}" (← docOf env w.name))
  -- The decisions over the same inputs, in one table; a state machine as its diagram.
  let decisions := here.filterMap fun w => do
    let inputs ← w.decisionInputs loaded
    let binders := w.info.type.getForallBinderNames
    return (w, (inputs.zip binders).map fun (type, binder) => (type, inputHeader type binder))
  let mut drawn : Array Name := #[]
  for (w, inputs) in decisions do
    if drawn.contains w.name then continue
    let headers := inputs.map Prod.snd
    if let some (state, event) := machine? w.info.type then
      drawn := drawn.push w.name
      let states := (valuesOf env state).toArray
      let events := valuesOf env event
      let labels ← computed w.name (states.mapM (render env))
      let mut diagram := labels.mapIdx fun i label => s!"  state \"{diagramLabel label}\" as s{i}"
      let mut refused := #[]
      for i in [:states.size] do
        for e in events do
          let eventLabel ← computed w.name (render env e)
          let answer ← loaded.reduce w.name #[states[i]!, e]
          match answer.getAppFn with
          | .const ``Except.error _ => refused := refused.push [labels[i]!, eventLabel, ← computed w.name (render env answer)]
          | _ =>
            let next := if answer.isAppOf ``Except.ok then answer.appArg! else answer
            let some target := states.idxOf? next
              | throw <| IO.userError s!"{w.name}: transition returned no state"
            diagram := diagram.push s!"  s{i} --> s{target} : {diagramLabel eventLabel}"
      out := out.push (captioned s!"**{escape (words w.name)}**" (← docOf env w.name))
      out := out.push ("```mermaid\nstateDiagram-v2\n" ++ "\n".intercalate diagram.toList ++ "\n```")
      if !refused.isEmpty then
        out := out.push (table (headers ++ ["answer"]) refused.toList)
      continue
    let group := (decisions.filter fun (other, args) =>
      args == inputs && (machine? other.info.type).isNone).map (·.1)
    drawn := drawn ++ group.map (·.name)
    let mut rows := #[]
    for combination in combinations env (inputs.map Prod.fst) do
      let mut row ← computed w.name (combination.mapM (render env))
      for g in group do
        row := row ++ [← evaluate loaded g.name combination]
      rows := rows.push row
    out := out.push (table (headers ++ group.toList.map (words ·.name)) rows.toList)
    let mut legend := #[]
    for g in group do
      legend := legend.push ("- " ++ captioned (escape (words g.name)) (← docOf env g.name))
    out := out.push ("\n".intercalate legend.toList)
  -- The rules and the rejected designs.
  for w in here do
    let .thmInfo _ := w.info | continue
    let doc ← docOf env w.name
    match w.name with
    | .str _ last =>
      if last.startsWith "not_" then out := out.push (captioned s!"✗ **{escape (words (Name.mkSimple (last.drop 4).toString))}**, rejected" doc)
      else out := out.push (captioned s!"✓ **{escape (words w.name)}**" doc)
    | _ => pure ()
  return "\n\n".intercalate out.toList

/-- A structure's propositional fields, in the context of its parameters and earlier fields. -/
private def premises (loaded : Loaded) (name : Name) : IO (Array (Name × String)) := do
  let env := loaded.env
  let fields := getStructureFields env name
  let ctor := getStructureCtor env name
  loaded.meta <| Meta.forallTelescope ctor.type fun args _ => do
    let mut out := #[]
    for field in fields, arg in args.toList.drop ctor.numParams do
      let type := (← Meta.inferType arg).consumeTypeAnnotations
      if ← Meta.isProp type then
        let doc ← docOf env ((getProjFnForField? env name field).getD (name ++ field))
        let text ← if doc.isEmpty then
          pure (escape (oneLine (← Meta.ppExpr type).pretty))
        else pure doc
        out := out.push (field, text)
    return out

/-- The view of one proof module: its premises, theorems and axiom dependencies. -/
def viewProofs (loaded : Loaded) (module : Name) : IO String := do
  let env := loaded.env
  let mut out := #[]
  let doc := (getModuleDoc? env module).map (·.toList.map (·.doc)) |>.getD []
  for d in doc do
    out := out.push ("\n".intercalate ((d.trimAscii.toString.splitOn "\n").map fun l => if l.startsWith "#" then "#" ++ l else l))
  if doc.isEmpty then out := out.push s!"## {escape module.toString}"
  for w in loaded.written do
    if w.module != module then continue
    if isStructure env w.name then
      let fields ← premises loaded w.name
      if fields.isEmpty then continue
      let label := captioned s!"**{escape (title w.name)}**" (← docOf env w.name)
      let rows := fields.map fun (name, text) => captioned s!"- Premise **{escape (words name)}**" text
      out := out.push (label ++ "\n\n" ++ "\n".intercalate rows.toList)
    else if let some proof ← loaded.meta (w.proofAxioms env) then
      let mark := if usesOutsideAxioms proof.axioms then "⚠" else "✓"
      let axioms := if proof.axioms.isEmpty then "none" else
        ", ".intercalate (proof.axioms.toList.map fun name => s!"`{name}`")
      let label := s!"{mark} **{escape (words w.name)}** (axioms: {axioms})"
      out := out.push (captioned label (← docOf env w.name))
    else if let .defnInfo d := w.info then
      if !w.standsAlone env || isInstanceAnywhere env w.name then continue
      let doc ← docOf env w.name
      let text ← if doc.isEmpty then
        pure (codeSpan (oneLine (← loaded.meta (Meta.ppExpr d.type)).pretty))
      else pure doc
      out := out.push (captioned s!"- Definition **{escape (words w.name)}**" text)
  return "\n\n".intercalate out.toList

/-- Draws the ledger and its proof libraries as Markdown. -/
def view (config : Config) : IO UInt32 := do
  let loaded ← config.load
  let mut pages := #["# The ledger"]
  for module in loaded.modules do
    pages := pages.push (← viewModule loaded module)
  for module in loaded.proofs do
    pages := pages.push (← viewProofs loaded module)
  IO.println ("\n\n".intercalate pages.toList)
  return 0

end TeslaValve
