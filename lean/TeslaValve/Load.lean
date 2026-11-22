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

/-- The modules of a library: every file under its directory. -/
def modulesOf (library : Name) : IO (Array Name) := do
  let dir := (modToFilePath "." library "lean").withExtension ""
  if !(← dir.isDir) then return #[]
  modulesUnder dir library

/-- The module a declaration stands in. -/
def moduleOf (env : Environment) (name : Name) : Option Name := do
  let idx ← env.getModuleIdxFor? name
  env.header.moduleNames[idx.toNat]?

/-- The name a text starts with, read as Lean reads it: dotted, a part of it in `«»`
where it is no identifier. -/
def leadingName (text : String) : Name := Id.run do
  let mut name := ""
  let mut quoted := false
  for c in text.toList do
    if c == '«' then quoted := true
    else if c == '»' then quoted := false
    else if !(quoted || isIdRest c || c == '.') then break
    name := name.push c
  return (name.dropEndWhile (· == '.')).toString.toName

/-- Where a declaration's name stands in its module, if the author wrote it there. What
the compiler made, as a derived instance or a matcher, has another token there. -/
def authoredAt (env : Environment) (source : Array String) (name : Name) : Option Position := do
  let ranges ← declRangeExt.find? env name
  let stands := ranges.selectionRange.pos
  let token := leadingName ((source[stands.line - 1]?.getD "").drop stands.column).toString
  let token := token.replacePrefix `_root_ .anonymous
  if !token.isAnonymous && token.isSuffixOf (privateToUserName name) then some stands else none

/-- Whether a place in the source is the `DecidableEq` of a `deriving` clause, where the
instance that clause derives and its function stand. A handwritten instance stands at
`instance`. -/
def derivesDecidableEq (source : Array String) (stands : Position) : Bool :=
  let line := source[stands.line - 1]?.getD ""
  let before := (line.take stands.column).toString
  leadingName (line.drop stands.column).toString == `DecidableEq && (before.splitOn "deriving").length > 1

/-- Where a module's source holds an `example`. Lean checks one and drops it, so the
build holds nothing of it for the check to read. -/
def examplesIn (env : Environment) (text : String) : IO (Array Position) := do
  let input := Parser.mkInputContext text "ledger"
  let (_, start, log) ← Parser.parseHeader input
  let mut state := start
  let mut messages := log
  let mut found := #[]
  repeat
    let (command, next, logged) := Parser.parseCommand input { env, options := {} } state messages
    state := next
    messages := logged
    if Parser.isTerminalCommand command then break
    -- An `example` may stand inside another command, as in a `mutual` block.
    if let some stated := command.find? (·.isOfKind ``Parser.Command.example) then
      if let some pos := stated.getPos? then found := found.push (input.fileMap.toPosition pos)
  return found

/-- A declaration as its author wrote it. -/
structure Written where
  module : Name
  name : Name
  info : ConstantInfo
  pos : Position

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
  for module in all do
    let text ← IO.FS.readFile (modToFilePath "." module "lean")
    sources := sources.insert module (text.splitOn "\n").toArray
    examples := examples ++ (← examplesIn env text).map (module, ·)
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
    -- instance is, unless a `deriving DecidableEq` clause made it, or it
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
      if serves || derivesDecidableEq (sources.getD module #[]) ranges.range.pos then
        made := made.push (module, name, info)
      else written := written.push { module, name, info, pos := ranges.selectionRange.pos }
    | none, none => made := made.push (module, name, info)
  let order (a b : Written) := a.module.toString < b.module.toString ||
    (a.module == b.module && (a.pos.line < b.pos.line || (a.pos.line == b.pos.line && a.pos.column < b.pos.column)))
  return { env, modules, proofs, roots, written := written.qsort order, made, examples }

/-- Whether a declaration stands in one of the ledger's modules. -/
def Loaded.owns (loaded : Loaded) (name : Name) : Bool :=
  (moduleOf loaded.env name).any loaded.modules.contains

/-- Runs a meta program against the loaded environment. -/
def Loaded.meta (loaded : Loaded) (x : MetaM α) : IO α := do
  let ctx : Core.Context := { fileName := "ledger", fileMap := default, maxHeartbeats := 0 }
  let (a, _) ← (x.run' {} {}).toIO ctx { env := loaded.env }
  return a

/-- The arguments of a function type and its result. It stops at a dependent arrow,
which is then the result. -/
partial def arrows (type : Expr) : Array Expr × Expr :=
  match type with
  | .forallE _ arg body _ =>
    if body.hasLooseBVars then (#[], type)
    else let (args, result) := arrows body; (#[arg] ++ args, result)
  | _ => (#[], type)

end TeslaValve
