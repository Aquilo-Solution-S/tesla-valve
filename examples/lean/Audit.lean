import Lean
open Lean

/-- A part of the spec, by the prefix of its modules, and the code that holds it. -/
structure Scope where
  spec : Name
  code : List System.FilePath

/-- Every module under a directory of the spec, read from the tree. -/
partial def modulesUnder (dir : System.FilePath) (pre : Name) : IO (Array Name) := do
  let mut found := #[]
  for entry in ← dir.readDir do
    if ← entry.path.isDir then
      found := found ++ (← modulesUnder entry.path (pre.str entry.fileName))
    else if entry.path.extension == some "lean" then
      found := found.push (pre.str (entry.path.fileStem.getD ""))
  return found

/-- Every file under a path of the code. -/
partial def filesUnder (path : System.FilePath) : IO (Array System.FilePath) := do
  if !(← path.isDir) then return #[path]
  let mut found := #[]
  for entry in ← path.readDir do
    found := found ++ (← filesUnder entry.path)
  return found

-- region: refusal
/-- The constants a declaration names, in its type and in its value. -/
def named (info : ConstantInfo) : Array Name :=
  info.type.getUsedConstants ++ (info.value?.map (·.getUsedConstants)).getD #[]

/-- Why a declaration of the model is refused, if it is. -/
def refusal (env : Environment) (name : Name) (info : ConstantInfo) : Option String :=
  if info matches .axiomInfo _ then some "is an axiom"
  else if info.isUnsafe then some "is unsafe"
  else if info matches .opaqueInfo _ then some "is partial or opaque"
  else if isNoncomputable env name then some "is noncomputable"
  else if (named info).any (· ∈ [``IO, ``EIO, ``BaseIO]) then some "does IO"
  else none
-- endregion

/-- The name a text starts with, read as Lean reads it: dotted, a part of it
in `«»` where it is no identifier. -/
def leadingName (text : String) : Name := Id.run do
  let mut name := ""
  let mut quoted := false
  for c in text.toList do
    if c == '«' then quoted := true
    else if c == '»' then quoted := false
    else if !(quoted || isIdRest c || c == '.') then break
    name := name.push c
  return (name.dropEndWhile (· == '.')).toString.toName

/-- The declarations a file of the code names: each `@holds <name>` in it. -/
def cited (text : String) : List Name :=
  ((text.splitOn "@holds ").tail.map leadingName).filter (!·.isAnonymous)

/-- What a declaration is stated in: its type, the body of a decision, and
what the constructors of a type take. Not a proof. Code that holds the
declaration holds the types and the decisions among these with it. -/
def statedIn (env : Environment) : ConstantInfo → Array Name
  | .thmInfo rule => rule.type.getUsedConstants
  | .inductInfo type => type.type.getUsedConstants ++ type.ctors.toArray.flatMap fun ctor =>
      ((env.find? ctor).map (·.type.getUsedConstants)).getD #[]
  | info => named info

/-- Whether the author wrote a declaration's name: it stands in the source
where the declaration does. `source` is the lines of its module. What the
compiler named, as a derived instance or a notation, has another token there. -/
def authored (env : Environment) (source : Array String) (name : Name) : Bool :=
  (declRangeExt.find? env name).any fun ranges =>
    let stands := ranges.selectionRange.pos
    let token := leadingName ((source[stands.line - 1]?.getD "").drop stands.column).toString
    let token := token.replacePrefix `_root_ .anonymous
    !token.isAnonymous && token.isSuffixOf name

/-- A declaration of the spec. -/
structure Declared where
  module : Name
  info : ConstantInfo
  owed : Bool

/-- Audits the spec that the library builds, and ties it to the code scope by
scope. A project calls this from a file of its own and leaves this one as it is. -/
def audit (library : Name) (scopes : List Scope) : IO UInt32 := do
  let root := modToFilePath "." library "lean"
  if ← root.pathExists then
    IO.eprintln s!"{root} is outside the glob {library}.+, so nothing builds it: move it under {library}/"
    return 1
  initSearchPath (← findSysroot)
  let modules ← modulesUnder (root.withExtension "") library
  let env ← importModules (modules.map ({ module := · })) {}
  let mut refused := 0
  let mut spec : Std.HashMap Name Declared := {}
  let mut sources : Std.HashMap Name (Array String) := {}
  for module in modules do
    let text ← IO.FS.readFile (modToFilePath "." module "lean")
    sources := sources.insert module (text.splitOn "\n").toArray
  for (name, info) in env.constants.map₁.toList do
    let some idx := env.getModuleIdxFor? name | continue
    let module := env.header.moduleNames[idx.toNat]!
    if !library.isPrefixOf module then continue
    -- Only what the compiler generated is skipped: a private name is the author's own.
    let written := privateToUserName name
    let authored := authored env (sources.getD module #[]) name
    if written.isInternal && !authored then continue
    if let some why := refusal env name info then
      IO.eprintln s!"{module}: {written} {why}"
      refused := refused + 1
    -- A constructor and a field belong to their type.
    let owed := authored && !isPrivateName name && !(info matches .ctorInfo _) && !env.isProjectionFn name
    spec := spec.insert name { module, info, owed }
  -- Each scope on its own: what its code names, and whether that holds its modules.
  let ordered := spec.toArray.qsort (·.1.toString < ·.1.toString)
  for scope in scopes do
    if !modules.any scope.spec.isPrefixOf then
      IO.eprintln s!"{scope.spec}: no module of the spec is under it"
      refused := refused + 1
    let mut held : Std.HashMap Name (Array String) := {}
    let mut todo := []
    for path in scope.code do
      for file in (← filesUnder path).qsort (·.toString < ·.toString) do
        let some text := String.fromUTF8? (← IO.FS.readBinFile file) | continue
        for name in cited text do
          match spec[name]? with
          | none =>
            IO.eprintln s!"{file}: names {name}, which the spec does not declare"
            refused := refused + 1
          | some declared =>
            if scope.spec.isPrefixOf declared.module then
              held := held.insert name ((held.getD name #[]).push s!"by {file}")
              todo := (name, name) :: todo
    -- A type or a decision of the scope is held with what is stated in it. A rule
    -- is held by its name alone.
    repeat
      let (name, root) :: rest := todo | break
      todo := rest
      let some declared := spec[name]? | continue
      for used in statedIn env declared.info do
        let some other := spec[used]? | continue
        if !scope.spec.isPrefixOf other.module || other.info matches .thmInfo _ || held.contains used then
          continue
        held := held.insert used #[s!"with {root}, {", ".intercalate (held.getD root #[]).toList}"]
        todo := (used, root) :: todo
    -- The map from the spec to this code, which owes every name of the scope.
    for (name, declared) in ordered do
      if !scope.spec.isPrefixOf declared.module || !declared.owed then continue
      match held[name]? with
      | some holders => IO.println s!"{declared.module}: {name} is held {", ".intercalate holders.toList}"
      | none =>
        IO.eprintln s!"{declared.module}: no code under {scope.code} names {name}"
        refused := refused + 1
  for module in modules.qsort (·.toString < ·.toString) do
    if !scopes.any (·.spec.isPrefixOf module) then IO.println s!"{module}: no scope lists it"
  return if refused == 0 then 0 else 1
