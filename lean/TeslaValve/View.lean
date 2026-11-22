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

/-- The docstring of a declaration, on one line. -/
def docOf (env : Environment) (name : Name) : IO String := do
  return oneLine ((← findDocString? env name).getD "")

/-- A label, and after it the docstring where there is one. -/
def captioned (label doc : String) : String :=
  if doc.isEmpty then label else s!"{label}: {doc}"

/-- A case or a field as a list item: its words, and its docstring where it has one. -/
def item (env : Environment) (label : String) (name : Name) : IO String := do
  return "- " ++ captioned label (← docOf env name)

/-- Every value of a closed choice, case by case in the order they are declared. -/
partial def valuesOf (env : Environment) : Expr → List Expr
  | .const ``Bool [] => [mkConst ``Bool.true, mkConst ``Bool.false]
  | .const name [] => match env.find? name with
    | some (.inductInfo type) => type.ctors.flatMap fun ctor =>
      let args := match env.find? ctor with
        | some info => (arrows info.type).1.toList
        | none => []
      args.foldl (fun made arg => made.flatMap fun e => (valuesOf env arg).map (mkApp e ·)) [mkConst ctor]
    | _ => []
  | _ => []

/-- The types of a constructor's fields, after its parameters. -/
def fieldTypes (type : Expr) (params : Nat) : List Expr :=
  match type, params with
  | .forallE _ _ body _, n + 1 => fieldTypes body n
  | .forallE _ field body _, 0 => field.consumeTypeAnnotations :: fieldTypes body 0
  | _, _ => []

/-- The items of a list the ledger computed, in order. -/
partial def listItems (e : Expr) : List Expr :=
  match e.getAppFn, e.getAppArgs with
  | .const ``List.cons _, #[_, head, tail] => head :: listItems tail
  | _, _ => []

/-- A value the ledger computed, in words. A shape shows its fields and not its invariant,
which is a proof. -/
partial def render (env : Environment) (e : Expr) : String :=
  let args := e.getAppArgs
  match e.getAppFn with
  | .const ``Option.none _ => "—"
  | .const ``Option.some _ => render env args.back!
  | .const ``Except.ok _ => render env args.back!
  | .const ``Except.error _ => s!"refused: {render env args.back!}"
  | .const ``Bool.true _ => "yes"
  | .const ``Bool.false _ => "no"
  | .const ``OfNat.ofNat _ => render env (args[1]?.getD e)
  | .lit (.natVal n) => toString n
  | .lit (.strVal s) => s.quote
  | .const ``List.nil _ => "[]"
  | .const ``List.cons _ => s!"[{", ".intercalate ((listItems e).map (render env))}]"
  | .const ctor _ => match env.find? ctor with
    | some (.ctorInfo info) =>
      let fields := args.extract info.numParams args.size
      if fields.isEmpty then caseLabel ctor
      else
        let names := if isStructure env info.induct then getStructureFields env info.induct else #[]
        if names.isEmpty then s!"{caseLabel ctor} ({", ".intercalate (fields.toList.map (render env))})"
        else
          let shown := ((names.toList.zip fields.toList).zip (fieldTypes info.type info.numParams)).filter
            fun (_, type) => !type.isAppOf ``Eq
          ", ".intercalate (shown.map fun ((field, v), _) => s!"{words field}: {render env v}")
    | _ => toString e
  | _ => toString e

/-- What a decision answers for each of its inputs. -/
def evaluate (loaded : Loaded) (decision : Name) (inputs : List Expr) : IO String :=
  loaded.meta do
    let answer ← Meta.reduce (mkAppN (mkConst decision) inputs.toArray)
    return render loaded.env answer

/-- Every combination of one value per type. -/
def combinations (env : Environment) (types : List Expr) : List (List Expr) :=
  types.foldr (fun type rest => (valuesOf env type).flatMap fun v => rest.map (v :: ·)) [[]]

/-- A table with a header row. -/
def table (header : List String) (rows : List (List String)) : String :=
  let escape (cell : String) :=
    cell.replace "\\" "\\\\" |>.replace "|" "\\|" |>.replace "`" "\\`" |>.replace "*" "\\*"
      |>.replace "_" "\\_" |>.replace "[" "\\[" |>.replace "<" "\\<" |>.replace "&" "\\&"
      |>.replace "\r" "" |>.replace "\n" "<br>"
  let line (cells : List String) := "| " ++ " | ".intercalate (cells.map escape) ++ " |"
  "\n".intercalate ([line header, line (header.map fun _ => "---")] ++ rows.map line)

/-- The name of a type, in words. -/
def typeWords (type : Expr) : String :=
  match type.getAppFn with
  | .const name _ => words name
  | _ => toString type

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
  if doc.isEmpty then out := out.push s!"## {module}"
  -- A case or a field is drawn with its type, not on its own.
  let here := loaded.written.filter fun w =>
    w.module == module && w.standsAlone env
  -- The choices and shapes, with their cases and fields.
  for w in here do
    let .inductInfo type := w.info | continue
    let mut block := #[captioned s!"**{title w.name}**" (← docOf env w.name), ""]
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
    out := out.push (captioned s!"**{words w.name}** = {← evaluate loaded w.name []}" (← docOf env w.name))
  -- The decisions over the same inputs, in one table; a state machine as its diagram.
  let decisions := here.filterMap fun w => (w.decisionInputs loaded).map (w, ·)
  let mut drawn : Array Name := #[]
  for (w, inputs) in decisions do
    if drawn.contains w.name then continue
    if let some (state, event) := machine? w.info.type then
      drawn := drawn.push w.name
      let states := (valuesOf env state).toArray
      let events := valuesOf env event
      let labels := states.map (render env)
      let mut diagram := labels.mapIdx fun i label => s!"  state \"{diagramLabel label}\" as s{i}"
      let mut refused := #[]
      for i in [:states.size] do
        for e in events do
          let answer ← loaded.meta (Meta.reduce (mkAppN (mkConst w.name) #[states[i]!, e]))
          match answer.getAppFn with
          | .const ``Except.error _ => refused := refused.push [labels[i]!, render env e, render env answer]
          | _ =>
            let next := if answer.isAppOf ``Except.ok then answer.appArg! else answer
            let some target := states.idxOf? next
              | throw <| IO.userError s!"{w.name}: transition returned no state"
            diagram := diagram.push s!"  s{i} --> s{target} : {diagramLabel (render env e)}"
      out := out.push (captioned s!"**{words w.name}**" (← docOf env w.name))
      out := out.push ("```mermaid\nstateDiagram-v2\n" ++ "\n".intercalate diagram.toList ++ "\n```")
      if !refused.isEmpty then
        out := out.push (table [typeWords state, typeWords event, "answer"] refused.toList)
      continue
    let group := (decisions.filter fun (other, args) =>
      args == inputs && (machine? other.info.type).isNone).map (·.1)
    drawn := drawn ++ group.map (·.name)
    let mut rows := #[]
    for combination in combinations env inputs do
      let mut row := combination.map (render env)
      for g in group do
        row := row ++ [← evaluate loaded g.name combination]
      rows := rows.push row
    out := out.push (table (inputs.map typeWords ++ group.toList.map (words ·.name)) rows.toList)
    let mut legend := #[]
    for g in group do
      legend := legend.push ("- " ++ captioned (words g.name) (← docOf env g.name))
    out := out.push ("\n".intercalate legend.toList)
  -- The rules and the rejected designs.
  for w in here do
    let .thmInfo _ := w.info | continue
    let doc ← docOf env w.name
    match w.name with
    | .str _ last =>
      if last.startsWith "not_" then out := out.push (captioned s!"✗ **{words (Name.mkSimple (last.drop 4).toString)}**, rejected" doc)
      else out := out.push (captioned s!"✓ **{words w.name}**" doc)
    | _ => pure ()
  return "\n\n".intercalate out.toList

/-- The view of one proof module: its title, and each rule it proves. -/
def viewProofs (loaded : Loaded) (module : Name) : IO String := do
  let env := loaded.env
  let mut out := #[]
  let doc := (getModuleDoc? env module).map (·.toList.map (·.doc)) |>.getD []
  for d in doc do
    out := out.push ("\n".intercalate ((d.trimAscii.toString.splitOn "\n").map fun l => if l.startsWith "#" then "#" ++ l else l))
  if doc.isEmpty then out := out.push s!"## {module}"
  for w in loaded.written do
    if w.module != module then continue
    let .thmInfo _ := w.info | continue
    out := out.push (captioned s!"✓ **{words w.name}**" (← docOf env w.name))
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
