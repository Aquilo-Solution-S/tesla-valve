import Lean
open Lean

/-! What the check and the view read: the modules of the ledger and of the proof libraries
beside it, read from the tree, and the declarations their authors wrote, as the build
produced them. -/

namespace TeslaValve

/-- Every module under a directory, read from the tree. -/
partial def modulesUnder (dir : System.FilePath) (pre : Name) : IO (Array Name) := do
  let mut found := #[]
  for entry in (← dir.readDir).qsort (·.fileName < ·.fileName) do
    if ← entry.path.isDir then
      found := found ++ (← modulesUnder entry.path (pre.str entry.fileName))
    else if entry.path.extension == some "lean" then
      found := found.push (pre.str (entry.path.fileStem.getD ""))
  return found

/-- The modules of a library: its root file and every file under its directory. -/
def modulesOf (library : Name) : IO (Array Name) := do
  let file := modToFilePath "." library "lean"
  let dir := file.withExtension ""
  let root := if ← file.pathExists then #[library] else #[]
  if ← dir.isDir then return root ++ (← modulesUnder dir library)
  return root

/-- The module a declaration stands in. -/
def moduleOf (env : Environment) (name : Name) : Option Name := do
  let idx ← env.getModuleIdxFor? name
  env.header.moduleNames[idx.toNat]?

/-- Reads one identifier with Lean's lexer, including dotted and escaped components. -/
def readName (env : Environment) (input : Parser.InputContext) (pos : String.Pos.Raw := 0) :
    Option (Name × String.Pos.Raw) := do
  let start := (Parser.mkParserState input.inputString).setPos pos
  let result := (Parser.rawIdentFn false).run input { env, options := {} } default start
  guard !result.hasError
  let .ident _ _ name _ := result.stxStack.back | none
  return (name, result.pos)

/-- Where a declaration's name stands in its module, if the author wrote it there. What
the compiler made, as a derived instance or a matcher, has another token there. -/
def authoredAt (env : Environment) (source : Array String) (name : Name) : Option Position := do
  let ranges ← declRangeExt.find? env name
  let stands := ranges.selectionRange.pos
  let text := ((source[stands.line - 1]?.getD "").drop stands.column).toString
  let (token, _) ← readName env (Parser.mkInputContext text "ledger")
  let token := token.replacePrefix `_root_ .anonymous
  if !token.isAnonymous && token.isSuffixOf (privateToUserName name) then some stands else none

/-- The evidence attached to source commands by the parser. Lean drops examples after
checking them. It places derived instances at the class names inside deriving clauses and
`deriving instance` commands. -/
structure SourceForms where
  examples : Array Position := #[]
  derivingClauses : Array (Position × Position) := #[]

partial def SourceForms.record (input : Parser.InputContext) (forms : SourceForms) : Syntax → SourceForms
  | stx@(.node _ kind args) => Id.run do
    let mut forms := forms
    if let (some start, some stop) := (stx.getPos?, stx.getTailPos?) then
      let pos := input.fileMap.toPosition start
      if kind == ``Parser.Command.example then
        forms := { forms with examples := forms.examples.push pos }
      else if (kind == ``Parser.Command.optDeriving || kind == ``Parser.Command.«deriving») && start < stop then
        forms := { forms with derivingClauses := forms.derivingClauses.push (pos, input.fileMap.toPosition stop) }
    return args.foldl (SourceForms.record input) forms
  | _ => forms

def sourceForms (env : Environment) (text : String) : IO SourceForms := do
  let input := Parser.mkInputContext text "ledger"
  let (_, start, log) ← Parser.parseHeader input
  let mut state := start
  let mut messages := log
  let mut forms := {}
  repeat
    let (command, next, logged) := Parser.parseCommand input { env, options := {} } state messages
    if Parser.isTerminalCommand command then break
    state := next
    messages := logged
    forms := forms.record input command
  return forms

/-- A declaration as its author wrote it. -/
structure Written where
  module : Name
  name : Name
  info : ConstantInfo
  pos : Position

def positionBefore (a b : Position) : Bool :=
  a.line < b.line || (a.line == b.line && a.column < b.column)

/-- What the libraries hold, loaded from the build: the ledger's modules and the proof
modules, the declarations written in their source, in source order, every other constant
the compiler made in them, and where their source holds an `example`. -/
structure Loaded where
  env : Environment
  /-- The ledger's modules, which the forms hold. -/
  modules : Array Name
  /-- The proof modules: loaded with the ledger, held to their proofs and docstrings. -/
  proofs : Array Name
  /-- The roots a link starts with: the ledger's and each proof library's. -/
  roots : List Name
  written : Array Written
  made : Array (Name × Name × ConstantInfo)
  examples : Array (Name × Position)

/-- Loads the modules as one environment, with the state of its extensions: which
constants are classes and instances, and their docstrings. The caller has called
`enableInitializersExecution`. -/
def load (modules : Array Name) (proofs : Array Name := #[]) (roots : List Name := []) : IO Loaded := do
  let all := modules ++ proofs
  let env ← importModules (all.map ({ module := · })) {} (loadExts := true)
  let mut sources : Std.HashMap Name (Array String) := {}
  let mut examples := #[]
  let mut derivingClauses : Std.HashMap Name (Array (Position × Position)) := {}
  for module in all do
    let text ← IO.FS.readFile (modToFilePath "." module "lean")
    sources := sources.insert module (text.splitOn "\n").toArray
    let forms ← sourceForms env text
    examples := examples ++ forms.examples.map (module, ·)
    derivingClauses := derivingClauses.insert module forms.derivingClauses
  let mut constants := #[]
  for (name, info) in env.constants.map₁.toList do
    let some module := moduleOf env name | continue
    if all.contains module then constants := constants.push (module, name, info)
  let named (module name : Name) := authoredAt env (sources.getD module #[]) name
  let authored : Std.HashSet Name := constants.foldl (init := {}) fun set (module, name, _) =>
    if (named module name).isSome then set.insert name else set
  let mut written := #[]
  let mut made := #[]
  for (module, name, info) in constants do
    -- A constant with a place in the source was written there, as an anonymous
    -- instance is, unless a deriving clause made it, or it
    -- serves a declaration whose name it extends, as the axiom of a `native_decide` does.
    let serves := Id.run do
      let mut pre := name.getPrefix
      while !pre.isAnonymous do
        if authored.contains pre then return true
        pre := pre.getPrefix
      return false
    match named module name, declRangeExt.find? env name with
    | some stands, _ => written := written.push { module, name, info, pos := stands }
    | none, some ranges =>
      if serves || (derivingClauses.getD module #[]).any (fun (start, stop) =>
        !positionBefore ranges.range.pos start && positionBefore ranges.range.pos stop) then
        made := made.push (module, name, info)
      else written := written.push { module, name, info, pos := ranges.selectionRange.pos }
    | none, none => made := made.push (module, name, info)
  let order (a b : Written) := a.module.toString < b.module.toString ||
    (a.module == b.module && positionBefore a.pos b.pos)
  return { env, modules, proofs, roots, written := written.qsort order, made, examples }

/-- Whether a declaration stands in one of the ledger's modules. -/
def Loaded.owns (loaded : Loaded) (name : Name) : Bool :=
  (moduleOf loaded.env name).any loaded.modules.contains

/-- Whether a written declaration stands on its own. Cases and fields belong to their type. -/
def Written.standsAlone (written : Written) (env : Environment) : Bool :=
  !(written.info matches .ctorInfo _) && !env.isProjectionFn written.name

/-- Runs a meta program against the loaded environment. -/
def Loaded.meta (loaded : Loaded) (x : MetaM α) : IO α := do
  let ctx : Core.Context := { fileName := "ledger", fileMap := default, maxHeartbeats := 0 }
  let (a, _) ← (x.run' {} {}).toIO ctx { env := loaded.env }
  return a

/-- Computes every value field of a declaration's result, including implicit fields. -/
def Loaded.reduce (loaded : Loaded) (name : Name) (inputs : Array Expr := #[]) : IO Expr :=
  loaded.meta (Meta.reduce (mkAppN (mkConst name) inputs) (explicitOnly := false))

/-- The arguments of a function type and its result. It stops at a dependent arrow,
which is then the result. -/
partial def arrows (type : Expr) : Array Expr × Expr :=
  match type with
  | .forallE _ arg body _ =>
    if body.hasLooseBVars then (#[], type)
    else let (args, result) := arrows body; (#[arg] ++ args, result)
  | _ => (#[], type)

end TeslaValve
