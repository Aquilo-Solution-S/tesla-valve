import TeslaValve.Load
open Lean

/-! The forms of the ledger, and the check that refuses every declaration outside them.

The ledger allows seven forms, so that a view can draw all of it by evaluation:
- a closed choice: an `inductive` whose cases carry nothing, or closed choices;
- a shape: a `structure` of ledger values, whose only invariant is a field
  `ok : decision fields = true`;
- a constant: a `def` of a ledger value, such as a number;
- a decision: a `def` whose inputs are closed choices and whose body matches them,
  case by case, into ledger values;
- a state machine: a decision `State → Event → State`, or `State → Event → Except Refusal State`
  where an event can be refused, whose events are a choice of their own; its name says what it
  decides;
- a rule: a `theorem` about the ledger, proved without `sorry`, `native_decide` or an
  axiom beyond Lean's three;
- a rejected design: a rule named `not_…`, which shows the alternative breaks the ledger.

A ledger value is a closed choice, a shape, `Nat`, `Bool`, an `Option` of a value, or an
`Except` of a closed choice and a value.

The Lean is the documentation. Every declaration has a docstring of one line that says
what it is, without a date, and a module's docstring is its title. A case or a field has
one only for what its name cannot say, such as a condition, a bound or a never: `notText`
says "A text whose bytes are not UTF-8", and `none` says nothing, because filler teaches a
reader to skip the lines that matter. A docstring names no person and tells no history,
such as who ruled a rule and when: git and the issue keep that.

A rule is linked by its full name in backticks, as `Shop.Stock.reserve`, in a docstring of
the ledger and in every file of the repository alike. The check refuses a link that
names neither a declaration nor a namespace of the ledger or of a proof library beside it.

A proof library holds the rules that need more than the forms, such as an induction over a
graph: its structures, classes and instances are its own business, and the check holds it
to its proofs and its docstrings alone. -/

namespace TeslaValve

/-- Why the check refuses a declaration. Each has its module under `Refused/`. -/
inductive Refusal where
  | isPrivate
  | isUnsafe
  | isAxiom
  | isPartial
  | isNoncomputable
  | isPolymorphic
  | isInstance
  | isClass
  | isAbbrev
  | isMeta
  | isExample
  | openChoice
  | openShape
  | openInput
  | openValue
  | operation
  | statement
  | assumed
  | undocumented
  | dangling
  | wordy
  | dated
  deriving DecidableEq, Repr, Inhabited

open Elab Term in
/-- Every case of `Refusal`, read from the type itself. -/
elab "every_refusal" : term => do
  let some (.inductInfo type) := (← getEnv).find? ``Refusal | throwError "Refusal is not declared"
  Meta.mkListLit (mkConst ``Refusal) (type.ctors.map mkConst)

/-- Every refusal, in the order the type declares them. -/
def Refusal.all : List Refusal := every_refusal

/-- A refusal's own name, as `isPrivate`: the name of the module under `Refused/` that shows it. -/
def Refusal.name (why : Refusal) : String := ((reprStr why).splitOn ".").getLast!

/-- What a refusal says, after the declaration's name. -/
def Refusal.says : Refusal → String
  | .isPrivate => "is private: every declaration of the ledger is one another may name"
  | .isUnsafe => "is unsafe"
  | .isAxiom => "is an axiom: an outside fact is a hypothesis of the rule that needs it"
  | .isPartial => "is partial or opaque: a decision of the ledger ends and evaluates"
  | .isNoncomputable => "is noncomputable: a decision of the ledger evaluates"
  | .isPolymorphic => "takes a type or a universe: the ledger's forms are about its own types"
  | .isInstance => "is an instance: only `deriving DecidableEq` makes one"
  | .isClass => "is a class"
  | .isAbbrev => "is an abbrev: one name per thing"
  | .isMeta => "is meta code (syntax, a macro, a notation or an elaborator)"
  | .isExample => "is an example: a rule is a theorem, which others name and the view draws"
  | .openChoice => "is a choice with parameters, indices or recursion, or a case that carries what is not a closed choice"
  | .openShape => "is a shape with a field that is neither a ledger value nor an invariant `ok : decision fields = true`"
  | .openInput => "is a decision with an input that is not a closed choice"
  | .openValue => "has a type that is not a ledger value"
  | .operation => "uses an operation outside the forms: a decision matches its inputs case by case into ledger values"
  | .statement => "is a rule that names what is not in the ledger or in Lean's logic"
  | .assumed => "rests on `sorry`, `native_decide` or an axiom beyond propext, Quot.sound and Classical.choice"
  | .undocumented => "has no docstring"
  | .dangling => "links a name in its docstring that neither the ledger nor a proof library declares"
  | .wordy => "has a docstring of more than one line: the Lean says the rest"
  | .dated => "has a date, as 2026-11-12 or 12.11.2026, in its docstring: git and the issue keep the history"

/-- Operations a decision or a constant may use beside the ledger's own declarations. -/
def operations : List Name := [
  ``Bool, ``Bool.true, ``Bool.false, ``and, ``or, ``not,
  ``Nat, ``OfNat.ofNat, ``instOfNatNat,
  ``Option, ``Option.some, ``Option.none,
  ``Except, ``Except.ok, ``Except.error,
  ``Unit, ``PUnit, ``Unit.unit, ``PUnit.unit]

/-- What a rule may say beside the operations and the ledger's own declarations. -/
def logic : List Name := [
  ``Eq, ``Ne, ``Not, ``And, ``Or, ``Iff, ``Exists, ``True, ``False,
  ``LE.le, ``LT.lt, ``instLENat, ``instLTNat]

/-- The axioms Lean itself rests on. -/
def leansAxioms : List Name := [``propext, ``Quot.sound, ``Classical.choice]

/-- A closed choice of the loaded library: an inductive without parameters, indices or
recursion, whose cases carry only closed choices, or `Bool`. -/
partial def closed (loaded : Loaded) : Expr → Bool
  | .const ``Bool [] => true
  | .const name [] => loaded.owns name && !isStructure loaded.env name &&
    match loaded.env.find? name with
    | some (.inductInfo type) =>
      type.numParams == 0 && type.numIndices == 0 && !type.isRec && type.all.length == 1 &&
      type.ctors.all fun ctor => match loaded.env.find? ctor with
        | some info => let (args, result) := arrows info.type; result == .const name [] && args.all (closed loaded)
        | none => false
    | _ => false
  | _ => false

mutual
/-- A ledger value: a closed choice (`Bool` among them), a shape, `Nat`, an `Option` of
a value, or an `Except` of a closed choice and a value. -/
partial def value (loaded : Loaded) : Expr → Bool
  | .const ``Nat [] => true
  | type@(.const name []) => closed loaded type || shape loaded name
  | .app (.const ``Option [_]) inner => value loaded inner
  | .app (.app (.const ``Except [_, _]) refusal) inner => closed loaded refusal && value loaded inner
  | _ => false

/-- A shape of the loaded library: a structure without parameters or recursion whose
fields are ledger values or invariants. -/
partial def shape (loaded : Loaded) (name : Name) : Bool :=
  loaded.owns name && isStructure loaded.env name && !isClass loaded.env name &&
  match loaded.env.find? name with
  | some (.inductInfo type) =>
    type.numParams == 0 && type.numIndices == 0 && !type.isRec &&
    type.ctors.all fun ctor => (loaded.env.find? ctor).any fun info => fields info.type
  | _ => false
where
  /-- Each field of a constructor's type, through to the shape it makes. -/
  fields : Expr → Bool
    | .forallE _ field rest _ => (!field.hasLooseBVars && value loaded field || invariant field) && fields rest
    | _ => true
  /-- `ok : decision fields = true`, where the decision is the ledger's. -/
  invariant : Expr → Bool
    | .app (.app (.app (.const ``Eq [_]) (.const ``Bool [])) check) (.const ``Bool.true []) =>
      (match check.getAppFn with | .const decision _ => loaded.owns decision | _ => false) &&
      check.getAppArgs.all (·.isBVar)
    | _ => false
end

/-- Whether a type takes a type as an argument, as `{α : Type} → α → α` does. -/
partial def takesType : Expr → Bool
  | .forallE _ arg body _ => (arrows arg).2.isSort || takesType body
  | _ => false

/-- Whether a constant is meta code: syntax, a macro, a notation or an elaborator, each of
a type of Lean's own. A proof's term may name Lean's lemmas, as one by `omega` does. -/
def isMetaCode (info : ConstantInfo) : Bool :=
  info.type.getUsedConstants.any (`Lean).isPrefixOf

/-- Whether every name a term uses is the ledger's own or among the allowed ones. -/
def within (loaded : Loaded) (allowed : List Name) (term : Expr) : Bool :=
  term.getUsedConstants.all fun name => loaded.owns name || allowed.contains name

/-- Whether a constant rests on `sorry`, `native_decide` or an axiom beyond Lean's three,
through anything it names: a proof the compiler split off, as an invariant's, too. -/
def rests (name : Name) : CoreM Bool := do
  return (← collectAxioms name).any (!leansAxioms.contains ·)

/-- Why a declaration its author wrote is refused, if it is: the first reason. -/
def refusal (loaded : Loaded) (written : Written) : CoreM (Option Refusal) := do
  let env := loaded.env
  let name := written.name
  let info := written.info
  if isPrivateName name then return some .isPrivate
  if info.isUnsafe then return some .isUnsafe
  if info matches .axiomInfo _ then return some .isAxiom
  if info matches .opaqueInfo _ then return some .isPartial
  if isMetaCode info then return some .isMeta
  if Meta.isInstanceCore env name then return some .isInstance
  if isNoncomputable env name then return some .isNoncomputable
  if !info.levelParams.isEmpty then return some .isPolymorphic
  let form : Option Refusal := match info with
    | .inductInfo _ =>
      if isClass env name then some .isClass
      else if isStructure env name then (if shape loaded name then none else some .openShape)
      else if closed loaded (.const name []) then none else some .openChoice
    | .defnInfo def_ =>
      if getReducibilityStatusCore env name == .reducible then some .isAbbrev
      else
        let (args, result) := arrows def_.type
        if takesType def_.type then some .isPolymorphic
        else if !args.all (closed loaded) then some .openInput
        else if !value loaded result then some .openValue
        else if !within loaded operations def_.value then some .operation
        else none
    | .thmInfo rule =>
      if takesType rule.type then some .isPolymorphic
      else if within loaded (operations ++ logic) rule.type then none else some .statement
    | _ => none
  if form.isSome then return form
  if ← rests name then return some .assumed
  if (← findDocString? env name).isNone then return some .undocumented
  return none

/-- A refusal of one declaration. -/
structure Refused where
  module : Name
  name : Name
  why : Refusal

/-- The names a docstring links: each code span that starts with one of the roots and a dot. -/
def links (roots : List Name) (doc : String) : List Name := Id.run do
  let mut found := []
  let mut inside := false
  for span in doc.splitOn "`" do
    if inside && roots.any (span.startsWith s!"{·}.") && !span.contains ' ' then
      found := span.toName :: found
    inside := !inside
  return found

/-- Whether a docstring links a name that is neither a declaration nor a namespace. -/
def dangles (env : Environment) (roots : List Name) (doc : String) : Bool :=
  (links roots doc).any fun name => !env.contains name && !env.isNamespace name

/-- Whether characters spell a date, as `2026-11-12` or `12.11.2026`. -/
def isDate : List Char → Bool
  | [a, b, c, d, '-', e, f, '-', g, h] => [a, b, c, d, e, f, g, h].all Char.isDigit
  | [a, b, '.', c, d, '.', e, f, g, h] => [a, b, c, d, e, f, g, h].all Char.isDigit
  | _ => false

/-- Whether a text holds a date. -/
def dated (text : String) : Bool := Id.run do
  let chars := text.toList
  for i in [0:chars.length] do
    if isDate ((chars.drop i).take 10) then return true
  return false

/-- Why a declaration's docstring is refused, if it is. -/
def docRefusal (env : Environment) (roots : List Name) (doc : String) : Option Refusal :=
  if dangles env roots doc then some .dangling
  else if doc.trimAscii.toString.contains '\n' then some .wordy
  else if dated doc then some .dated
  else none

/-- Every refusal in the loaded libraries: each declaration of the ledger written in its
source that is outside the forms, each constant the compiler made that the forms do not
allow, each proof that rests on more than Lean's axioms, each `example`, and each
docstring outside its form, a module's too. -/
def refusals (loaded : Loaded) : IO (Array Refused) := do
  let mut found := #[]
  for written in loaded.written do
    let doc ← findDocString? loaded.env written.name
    let ofLedger := loaded.modules.contains written.module
    -- A case or a field takes the form of its type, and its docstring is its author's call.
    let why ← if written.info matches .ctorInfo _ || loaded.env.isProjectionFn written.name then
        pure none
      else if ofLedger then loaded.meta (refusal loaded written)
      else do pure (if ← loaded.meta (rests written.name) then some .assumed else none)
    let why := why.orElse fun _ => doc.bind (docRefusal loaded.env loaded.roots)
    if let some why := why then
      found := found.push { module := written.module, name := privateToUserName written.name, why }
  for (module, name, info) in loaded.made do
    if !loaded.modules.contains module then
      if ← loaded.meta (rests name) then
        found := found.push { module, name := privateToUserName name, why := .assumed }
      continue
    let ofLedger := match info.type with
      | .app (.const ``DecidableEq _) (.const type []) => loaded.owns type
      | _ => false
    let why : Option Refusal ←
      if isMetaCode info then pure (some .isMeta)
      -- What `deriving` makes for a type of the ledger: only `DecidableEq`.
      else if !name.isInternal && Meta.isInstanceCore loaded.env name && !ofLedger then pure (some .isInstance)
      else if ← loaded.meta (rests name) then pure (some .assumed)
      else pure none
    if let some why := why then
      found := found.push { module, name := privateToUserName name, why }
  for (module, pos) in loaded.examples do
    found := found.push { module, name := Name.mkSimple s!"example at line {pos.line}", why := .isExample }
  for module in loaded.modules ++ loaded.proofs do
    let docs := (getModuleDoc? loaded.env module).map (·.toList.map (·.doc)) |>.getD []
    if docs.any (dangles loaded.env loaded.roots) then
      found := found.push { module, name := module, why := .dangling }
    else if docs.any dated then
      found := found.push { module, name := module, why := .dated }
  return found

/-- Where the package stands in its repository, as `lean/`: empty at the repository's top. -/
def placeInRepository : IO String := do
  let place ← IO.Process.output { cmd := "git", args := #["rev-parse", "--show-prefix"] }
  if place.exitCode != 0 then
    throw <| IO.userError s!"git rev-parse: {place.stderr.trimAscii}"
  return place.stdout.trimAscii.toString

/-- Each backticked name that starts with one of the roots in the repository's tracked files
under `paths`, with the file and line it stands on. -/
def mentions (roots : List Name) (paths : Array String) : IO (Array (String × Name)) := do
  if roots.isEmpty then return #[]
  let top ← IO.Process.output { cmd := "git", args := #["rev-parse", "--show-toplevel"] }
  if top.exitCode != 0 then
    throw <| IO.userError s!"git rev-parse: {top.stderr.trimAscii}"
  let grep ← IO.Process.output {
    cmd := "git", cwd := top.stdout.trimAscii.toString,
    args := #["grep", "-n", "-I", "-o", "-E", s!"`({"|".intercalate (roots.map toString)})\\.[A-Za-z0-9_.']+`", "--"] ++ paths }
  -- `git grep` exits 1 when nothing matches, and above 1 when it could not search.
  if grep.exitCode > 1 then
    throw <| IO.userError s!"git grep: {grep.stderr.trimAscii}"
  return grep.stdout.splitOn "\n" |>.filter (· != "") |>.toArray.map fun line =>
    let parts := line.splitOn ":"
    (":".intercalate parts.dropLast, (parts.getLast!.drop 1 |>.dropEnd 1).toString.toName)

/-- The mentions under `paths` whose name the environment neither declares nor opens. -/
def dangling (env : Environment) (roots : List Name) (paths : Array String) : IO (Array (String × Name)) :=
  return (← mentions roots paths).filter fun (_, name) => !env.contains name && !env.isNamespace name

/-- What a project checks: its ledger, the proof libraries beside it, and the paths of the
repository whose links are not the project's, relative to the repository's top. -/
structure Config where
  ledger : Name
  proofs : List Name := []
  unscanned : List String := []

/-- Loads a project's libraries. -/
def Config.load (config : Config) : IO Loaded := do
  let proofs ← config.proofs.toArray.flatMapM modulesOf
  TeslaValve.load (← modulesOf config.ledger) proofs (config.ledger :: config.proofs)

/-- Checks the ledger: every declaration in its forms, every proof on Lean's axioms alone,
and every link to either resolves, in every tracked file of the repository. -/
def check (config : Config) : IO UInt32 := do
  let loaded ← config.load
  if loaded.modules.isEmpty then
    IO.eprintln s!"{config.ledger}: no module under {config.ledger}/, so nothing is checked"
    return 1
  let refused ← refusals loaded
  for r in refused do
    IO.eprintln s!"error: {r.module}: {r.name} {r.why.says}"
  let unscanned := config.unscanned.toArray.map (s!":!{·}")
  let unresolved ← dangling loaded.env loaded.roots (#["."] ++ unscanned)
  for (place, name) in unresolved do
    IO.eprintln s!"error: {place}: links `{name}`, which neither the ledger nor a proof library declares"
  if refused.isEmpty && unresolved.isEmpty then
    let proofs := if loaded.proofs.isEmpty then "" else s!", beside {loaded.proofs.size} proof modules"
    IO.println s!"{config.ledger}: {loaded.written.size} declarations in {loaded.modules.size} modules{proofs}, each in its form"
    return 0
  return 1

end TeslaValve
