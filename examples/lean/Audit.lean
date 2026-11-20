import Lean
open Lean

/-- Every module under a directory of the spec, read from the tree. -/
partial def modulesUnder (dir : System.FilePath) (pre : Name) : IO (Array Name) := do
  let mut found := #[]
  for entry in ← dir.readDir do
    if ← entry.path.isDir then
      found := found ++ (← modulesUnder entry.path (pre.str entry.fileName))
    else if entry.path.extension == some "lean" then
      found := found.push (pre.str (entry.path.fileStem.getD ""))
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

def main : IO UInt32 := do
  if ← System.FilePath.pathExists "Spec.lean" then
    IO.eprintln "Spec.lean is outside the glob Spec.+, so nothing builds it: move it under Spec/"
    return 1
  initSearchPath (← findSysroot)
  let modules ← modulesUnder "Spec" `Spec
  let env ← importModules (modules.map ({ module := · })) {}
  let mut refused := 0
  for (name, info) in env.constants.map₁.toList do
    let some idx := env.getModuleIdxFor? name | continue
    let module := env.header.moduleNames[idx.toNat]!
    -- A private name is the author's own; only what the compiler generated is skipped.
    let written := privateToUserName name
    if !(`Spec).isPrefixOf module || written.isInternal then continue
    if let some why := refusal env name info then
      IO.eprintln s!"{module}: {written} {why}"
      refused := refused + 1
  return if refused == 0 then 0 else 1
