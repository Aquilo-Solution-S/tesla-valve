import TeslaValve.Load
open Lean

/-! The forms of the ledger, and the check that refuses every declaration outside them.

The ledger allows seven forms, so that a view can draw all of it by evaluation:
- a closed choice: an `inductive` whose cases carry nothing, or closed choices;
- a shape: a `structure` of ledger values, whose only invariant is a field
  `ok : decision fields = true`;
- a constant: a `def` of a ledger value, such as a number;
- a decision: a `def` that matches closed inputs into ledger values and names
  a constructor at every pattern position in every alternative, down to
  constructor fields and inside nested matches;
- a state machine: a decision `State → Event → State`, or `State → Event → Except Refusal State`
  where an event can be refused, whose events are a choice of their own; its name says what it
  decides;
- a rule: a `theorem` about the ledger, proved without `sorry`, `native_decide` or an
  axiom beyond Lean's three;
- a rejected design: a rule named `not_…`, which shows the alternative breaks the ledger.

The check refuses a choice with at most one value and a structure with no fields.
A decision that returns `Except <Error> _` and both succeeds and refuses may name its
refusal with a one-value choice. The check also refuses a decision with the same result
for every input, a decision with an input that changes no result, a unary decision that maps its two input values one-to-one onto a
two-value choice or `Bool` (including a Bool identity or negation), and a constant equal
to `[]` or `none`.

A ledger value is a closed choice, a shape, `Nat`, `Bool`, a `String`, a `List` or an `Option`
of a value, or an `Except` of a closed choice and a value. An `Option` cannot directly
contain another `Option`. A string spells what another
system reads exactly, such as a key; a rule is a declaration, never a string.

The Lean is the documentation. Every declaration has a docstring of one line that says
what it is, without a date, and a module's docstring is its title. A case or a field has
one only for what its name cannot say, such as a condition, a bound or a never: `notText`
says "A text whose bytes are not UTF-8", and `none` says nothing, because filler teaches a
reader to skip the lines that matter. A docstring names no person and tells no history,
such as who ruled a rule and when: git and the issue keep that.

A rule is linked by its full name in backticks, as `Shop.Stock.reserve`, in a docstring of
the ledger and in every file of the repository alike. The check refuses a link that
does not resolve to a declaration, module or namespace owned by a configured library.
A namespace counts when it contains a declaration of that library. A written
inductive or structure contributes all its constructors, including an implicit
`mk`. Other compiler-generated declarations are refused.

A scope ties modules to the code that holds them: every declaration of its modules is named,
by its full name, in a file under the scope's paths, or is stated in one that is, as a
choice is in the decision over it. A rule, a theorem, is held by its name alone.

A proof library holds rules that need more than the forms, such as induction over a graph.
It uses ordinary Lean types and definitions. The checker audits its proofs and docstrings,
and refuses unsafe, partial, noncomputable or IO declarations. Each configured proof
library must contribute a theorem. The view shows structure premises with their
docstrings or propositions. The check and view list each theorem's axioms, and the
check also counts proof theorems by axiom.

The check guards against mistakes in trusted source. It relies on Lean's declaration
ranges and authored name prefixes to distinguish generated declarations, and on kernel
checking for proofs. Source that tampers with that metadata or sets
`debug.skipKernelTC` is outside that guarantee. -/

namespace TeslaValve

/-- Why the check refuses a declaration. Each has its module under `TeslaValve/Test/Refused/`. -/
inductive Refusal where
  | isPrivate
  | isUnsafe
  | isAxiom
  | isPartial
  | isNoncomputable
  | doesIO
  | isPolymorphic
  | isInstance
  | isClass
  | isAbbrev
  | isMeta
  | isExample
  | openChoice
  | singletonChoice
  | openShape
  | openInput
  | openValue
  | operation
  | constantDecision
  | idleInput
  | relabelDecision
  | emptyConstant
  | unusedType
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

/-- A refusal's own name, as `isPrivate`: the name of the module under `TeslaValve/Test/Refused/` that shows it. -/
def Refusal.name (why : Refusal) : String := ((reprStr why).splitOn ".").getLast!

/-- What a refusal says, after the declaration's name. -/
def Refusal.says : Refusal → String
  | .isPrivate => "is private: every declaration of the ledger is one another may name"
  | .isUnsafe => "is unsafe"
  | .isAxiom => "is an axiom: an outside fact is a hypothesis of the rule that needs it"
  | .isPartial => "is partial or opaque: a decision of the ledger ends and evaluates"
  | .isNoncomputable => "is noncomputable: a decision of the ledger evaluates"
  | .doesIO => "does IO: what the ledger states holds without running anything"
  | .isPolymorphic => "takes a type or a universe: the ledger's forms are about its own types"
  | .isInstance => "is an instance: only `deriving DecidableEq` makes one"
  | .isClass => "is a class"
  | .isAbbrev => "is an abbrev or has a reducibility override: use an ordinary def"
  | .isMeta => "is meta code (syntax, a macro, a notation or an elaborator)"
  | .isExample => "is an example: a rule is a theorem, which others name and the view draws"
  | .openChoice => "is a choice with parameters, indices or recursion, or a case that carries what is not a closed choice"
  | .singletonChoice => "has at most one value. Give the type fields or cases that distinguish values, use a one-value choice in a decision that returns `Except <Error> _` and both succeeds and refuses, or state the rule in a theorem"
  | .openShape => "is a shape with a field that is neither a ledger value nor an invariant `ok : decision fields = true`"
  | .openInput => "is a decision with an input that is not a closed choice"
  | .openValue => "has a type that is not a ledger value"
  | .operation => "uses an operation outside the forms: a decision matches its inputs into ledger values with constructors at every pattern position"
  | .constantDecision => "returns the same value for every input. Write a constant or match inputs that change the result"
  | .idleInput => "has an input that changes no result. Drop the input, or match it where it changes the result"
  | .relabelDecision => "only relabels the two values of its input. Use the input directly (write `!input` for the negation), or keep the rule as one comment at its holder. In a shape, drop a field that can only hold one value"
  | .emptyConstant => "is an empty list or absent option. Write `[]` or `none` at the use site"
  | .unusedType => "is a choice or a shape that no other declaration uses, so it only gives a link a target. Use it in the decision or theorem that holds its rule, or keep the rule as one comment at its holder"
  | .statement => "is a rule that names what is not in the ledger or in Lean's logic"
  | .assumed => "rests on `sorry`, `native_decide` or an axiom beyond propext, Quot.sound and Classical.choice"
  | .undocumented => "has no docstring"
  | .dangling => "links a name in its docstring that neither the ledger nor a proof library declares"
  | .wordy => "has a docstring of more than one line: the Lean says the rest"
  | .dated => "has a date, as 2026-11-12 or 12.11.2026, in its docstring: git and the issue keep the history"

/-- Whether a refusal holds in a proof library too, whose structures, classes and examples
are its own business: what holds there is that every proof is a proof and every docstring
in its form. -/
def Refusal.inProofs : Refusal → Bool
  | .isPrivate => false
  | .isUnsafe => true
  | .isAxiom => true
  | .isPartial => true
  | .isNoncomputable => true
  | .doesIO => true
  | .isPolymorphic => false
  | .isInstance => false
  | .isClass => false
  | .isAbbrev => false
  | .isMeta => false
  | .isExample => false
  | .openChoice => false
  | .singletonChoice => false
  | .openShape => false
  | .openInput => false
  | .openValue => false
  | .operation => false
  | .constantDecision => false
  | .idleInput => false
  | .relabelDecision => false
  | .emptyConstant => false
  | .unusedType => false
  | .statement => false
  | .assumed => true
  | .undocumented => false
  | .dangling => true
  | .wordy => true
  | .dated => true

/-- Operations a decision or a constant may use beside the ledger's own declarations. -/
def operations : List Name := [
  ``Bool, ``Bool.true, ``Bool.false, ``and, ``or, ``not,
  ``Nat, ``OfNat.ofNat, ``instOfNatNat, ``String,
  ``List, ``List.cons, ``List.nil,
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

/-- Every combination of one value per type. -/
def combinations (env : Environment) (types : List Expr) : List (List Expr) :=
  types.foldr (fun type rest => (valuesOf env type).flatMap fun v => rest.map (v :: ·)) [[]]

/-- Whether every name a term uses is the ledger's own or among the allowed ones. -/
def within (loaded : Loaded) (allowed : List Name) (term : Expr) : Bool :=
  term.getUsedConstants.all fun name => loaded.owns name || allowed.contains name

/-- The binder types of a matcher, whose alternatives return the motive applied
to their original patterns. Explicit or-patterns have a binder per pattern. -/
private partial def binders : Expr → Array Expr
  | .forallE _ type rest _ => #[type] ++ binders rest
  | _ => #[]

private partial def binderResult : Expr → Expr
  | .forallE _ _ rest _ => binderResult rest
  | result => result

private partial def constructorPattern (env : Environment) (pattern : Expr) : Bool :=
  match env.find? pattern.getAppFn.constName with
  | some (.ctorInfo ctor) =>
    let args := pattern.getAppArgs
    (args.extract ctor.numParams args.size).all (constructorPattern env)
  | _ => false

private def hasNonConstructorPattern (env : Environment) (name : Name) : Bool := Id.run do
  let some matcher := Meta.getMatcherInfoCore? env name | return false
  let some info := env.find? name | return true
  let types := binders info.type
  return (types.extract matcher.getFirstAltPos matcher.arity).any fun alt =>
    let patterns := (binderResult alt).getAppArgs
    patterns.size != matcher.numDiscrs || !patterns.all (constructorPattern env)

/-- A decision starts by matching an input. -/
partial def matchesInputs (env : Environment) (term : Expr) (inputs : Nat) : Bool :=
  match term.consumeMData with
  | .lam _ _ body _ => matchesInputs env body inputs
  | body => match Meta.isMatcherAppCore? env body with
    | some matcher =>
      let discrs := body.getAppArgs.extract matcher.getFirstDiscrPos matcher.getFirstAltPos
      body.getAppNumArgs == matcher.arity && discrs.any (fun
        | .bvar i => i < inputs
        | _ => false)
    | none => false

def bodyInForm (loaded : Loaded) (d : DefinitionVal) (inputs : Array Expr) : Bool :=
  within loaded operations d.value && (inputs.isEmpty ||
    (matchesInputs loaded.env d.value inputs.size &&
      !d.value.getUsedConstants.any (hasNonConstructorPattern loaded.env)))

mutual
/-- A ledger value: a closed choice (`Bool` among them), a shape, `Nat`, a `String`, a `List`
or an `Option` of a value, or an `Except` of a closed choice and a value. -/
partial def value (loaded : Loaded) : Expr → Bool
  | .const ``Nat [] => true
  | .const ``String [] => true
  | type@(.const name []) => closed loaded type || shape loaded name
  | .app (.const ``Option [_]) inner => !inner.isAppOf ``Option && value loaded inner
  | .app (.const ``List [_]) inner => value loaded inner
  | .app (.app (.const ``Except [_, _]) refusal) inner => closed loaded refusal && value loaded inner
  | _ => false

/-- A shape of the loaded library: a structure without parameters or recursion whose
fields are ledger values or invariants. -/
partial def shape (loaded : Loaded) (name : Name) : Bool :=
  loaded.owns name && isStructure loaded.env name && !isClass loaded.env name &&
  match loaded.env.find? name with
  | some (.inductInfo type) =>
    type.numParams == 0 && type.numIndices == 0 && !type.isRec &&
    type.ctors.all fun ctor => (loaded.env.find? ctor).any fun info => fields 0 info.type
  | _ => false
where
  /-- Each field of a constructor's type, through to the shape it makes. -/
  fields : Nat → Expr → Bool
    | count, .forallE fieldName field rest _ =>
      let type := field.consumeTypeAnnotations
      ((!type.hasLooseBVars && value loaded type) ||
        (fieldName == `ok && invariant count type)) && fields (count + 1) rest
    | _, _ => true
  /-- The invariant applies a decision returning Bool to preceding fields. -/
  invariant : Nat → Expr → Bool
    | count, .app (.app (.app (.const ``Eq [_]) (.const ``Bool [])) check) (.const ``Bool.true []) => Id.run do
      let .const decision [] := check.getAppFn | return false
      let some (.defnInfo d) := loaded.env.find? decision | return false
      let (inputs, result) := arrows d.type
      return loaded.owns decision && !isPrivateName decision && !isNoncomputable loaded.env decision &&
        getReducibilityStatusCore loaded.env decision == .semireducible && d.levelParams.isEmpty &&
        !inputs.isEmpty && inputs.all (closed loaded) && result == mkConst ``Bool &&
        bodyInForm loaded d inputs &&
        check.getAppNumArgs == inputs.size && check.getAppArgs.all (fun
          | .bvar i => i < count
          | _ => false)
    | _, _ => false
end

/-- Whether a type takes a type as an argument, as `{α : Type} → α → α` does. -/
partial def takesType : Expr → Bool
  | .forallE _ arg body _ => (arrows arg).2.isSort || takesType body
  | _ => false

/-- The forms for constants and decisions share the result types and allowed operations. -/
def definitionForm (loaded : Loaded) (d : DefinitionVal) : Option Refusal :=
  let (args, result) := arrows d.type
  if takesType d.type then some .isPolymorphic
  else if !args.all (closed loaded) then some .openInput
  else if !value loaded result then some .openValue
  else if !bodyInForm loaded d args then some .operation
  else none

/-- Whether the input at `position` changes no result: for every value of the other inputs,
each of its values gives the same output. -/
private def idle (loaded : Loaded) (term : Expr) (inputs : Array Expr) (position : Nat) : MetaM Bool := do
  let first :: rest := valuesOf loaded.env inputs[position]! | return false
  let at_ (others : List Expr) (v : Expr) := mkAppN term (others.take position ++ v :: others.drop position).toArray
  (combinations loaded.env (inputs.toList.eraseIdx position)).allM fun others => do
    let output := at_ others first
    rest.allM fun v => Meta.isDefEq output (at_ others v)

/-- The output must carry a value or depend on each of the decision's inputs. -/
private def definitionContentRefusal (loaded : Loaded) (d : DefinitionVal) : MetaM (Option Refusal) := do
  let (inputs, result) := arrows d.type
  let term := mkConst d.name
  if inputs.isEmpty then
    let output ← Meta.whnf term
    return if output.isAppOf ``List.nil || output.isAppOf ``Option.none then some .emptyConstant else none
  let first :: rest := combinations loaded.env inputs.toList | return none
  let output := mkAppN term first.toArray
  if ← rest.allM (fun args => Meta.isDefEq output (mkAppN term args.toArray)) then
    return some .constantDecision
  if ← (List.range inputs.size).anyM (idle loaded term inputs) then
    return some .idleInput
  let #[_] := inputs | return none
  let [second] := rest | return none
  if !closed loaded result then return none
  let [left, right] := valuesOf loaded.env result | return none
  let other := mkAppN term second.toArray
  if ← (Meta.isDefEq output left <&&> Meta.isDefEq other right) <||>
      (Meta.isDefEq output right <&&> Meta.isDefEq other left) then
    return some .relabelDecision
  return none

/-- A named error carries meaning alongside the successes of an `Except` decision. -/
private def isDecisionError (loaded : Loaded) (choice : Name) : MetaM Bool := do
  for w in loaded.written do
    if !loaded.modules.contains w.module || !w.standsAlone loaded.env then continue
    let .defnInfo d := w.info | continue
    let (inputs, result) := arrows d.type
    let .app (.app (.const ``Except _) (.const errorType [])) _ := result | continue
    if errorType != choice || inputs.isEmpty || (definitionForm loaded d).isSome then continue
    let mut succeeds := false
    let mut refuses := false
    for args in combinations loaded.env inputs.toList do
      let answer ← Meta.whnf (mkAppN (mkConst w.name) args.toArray)
      succeeds := succeeds || answer.isAppOf ``Except.ok
      refuses := refuses || answer.isAppOf ``Except.error
      if succeeds && refuses then return true
  return false

/-- A decision and its finite inputs, as used by both output commands. -/
def Written.decisionInputs (w : Written) (loaded : Loaded) : Option (List Expr) := do
  guard (w.standsAlone loaded.env)
  let .defnInfo d := w.info | none
  let inputs := (arrows d.type).1
  guard (!inputs.isEmpty && (definitionForm loaded d).isNone)
  return inputs.toList

/-- Whether a constant is meta code: syntax, a macro, a notation or an elaborator, each of
a type of Lean's own. A proof's term may name Lean's lemmas, as one by `omega` does. -/
def isMetaCode (info : ConstantInfo) : Bool :=
  info.type.getUsedConstants.any (`Lean).isPrefixOf

/-- An inductive's field types live on its constructors. -/
def declarationTypes (env : Environment) (info : ConstantInfo) : Array Expr :=
  match info with
  | .inductInfo type => #[info.type] ++ type.ctors.toArray.filterMap (fun ctor =>
      (env.find? ctor).map (·.type))
  | _ => #[info.type]

/-- Default tactics remain in the types of parameters and constructor fields. -/
def defaultTactics (env : Environment) (info : ConstantInfo) : Array Name :=
  (declarationTypes env info).flatMap fun type => binders type #[]
where
  binders : Expr → Array Name → Array Name
    | .forallE _ arg rest _, names =>
      match arg.getAutoParamTactic? with
      | some (.const tactic _) => binders rest (names.push tactic)
      | _ => binders rest names
    | _, names => names

/-- Default tactics have syntax until a caller uses the default and Lean elaborates it. -/
def assumedDefault (env : Environment) (tactic : Name) : Bool :=
  match (Elab.evalSyntaxConstant env {} tactic).run with
  | .ok stx => (stx.find? fun s =>
      s.isOfKind ``Parser.Term.sorry || s.isOfKind ``Parser.Tactic.tacticSorry ||
      s.isOfKind ``Parser.Tactic.tacticAdmit || s.isOfKind ``Parser.Tactic.nativeDecide).isSome
  | .error _ => true

/-- A theorem and the axioms Lean collects from its statement and proof. -/
structure ProofAxioms where
  theoremName : Name
  module : Name
  axioms : Array Name

/-- Whether a name is an instance, a scoped one included: Lean finds a scoped instance only
while its namespace is open, so this opens each namespace the name is in. -/
def isInstanceAnywhere (env : Environment) (name : Name) : Bool :=
  let opened := name.getPrefix.components.foldl (init := (env, Name.anonymous))
    fun (env, scope) part =>
      let scope := scope ++ part
      (Meta.instanceExtension.activateScoped env scope, scope)
  Meta.isInstanceCore opened.1 name

/-- The inventory of a written theorem that contributes to its proof library. -/
def Written.proofAxioms (w : Written) (env : Environment) : MetaM (Option ProofAxioms) := do
  let .thmInfo _ := w.info | return none
  if !w.standsAlone env || isInstanceAnywhere env w.name then return none
  return some ⟨w.name, w.module, ← collectAxioms w.name⟩

/-- The axiom inventory of the authored theorems in the configured proof modules. -/
def proofAxioms (loaded : Loaded) (modules : Array Name) : IO (Array ProofAxioms) :=
  loaded.meta do
    let mut proofs := #[]
    for w in loaded.written do
      if !modules.contains w.module then continue
      if let some proof ← w.proofAxioms loaded.env then
        proofs := proofs.push proof
    return proofs

/-- Configured proof libraries with no authored theorem in their modules. -/
def emptyProofLibraries (libraries : List Name) (proofs : Array ProofAxioms) : List Name :=
  libraries.filter fun root => !proofs.any (root.isPrefixOf ·.module)

/-- The axiom counts followed by each theorem's inventory. -/
def proofReport (proofs : Array ProofAxioms) : String :=
  let free := proofs.countP (·.axioms.isEmpty)
  let counts := leansAxioms.map fun axiomName =>
    s!"{axiomName}: {proofs.countP (·.axioms.contains axiomName)}"
  let summary := s!"{proofs.size} proof theorems ({", ".intercalate (s!"axiom-free: {free}" :: counts)})"
  let lines := proofs.toList.map fun proof =>
    let axioms := if proof.axioms.isEmpty then "none" else
      ", ".intercalate (proof.axioms.toList.map Name.toString)
    s!"{proof.theoremName}: {axioms}"
  "\n".intercalate (summary :: lines)

/-- Whether an axiom inventory contains anything outside Lean's admitted axioms. -/
def usesOutsideAxioms (axioms : Array Name) : Bool :=
  axioms.any (!leansAxioms.contains ·)

/-- Whether a constant rests on more than Lean's axioms through what it names. -/
def rests (name : Name) : CoreM Bool := do
  return usesOutsideAxioms (← collectAxioms name)

/-- Whether the declaration uses IO in a value, a type, or the aliases and constructor fields of a type it uses. -/
partial def doesIO (env : Environment) (info : ConstantInfo) : Bool :=
  let names := (declarationTypes env info).flatMap Expr.getUsedConstants ++
    (info.value?.map Expr.getUsedConstants).getD #[]
  usesIO {} names.toList
where
  usesIO (seen : Std.HashSet Name) : List Name → Bool
    | [] => false
    | name :: more =>
      if name ∈ [``IO, ``EIO, ``BaseIO, ``IO.RealWorld] then true
      else if seen.contains name then usesIO seen more
      else
        let used := match env.find? name with
          | some (info@(.inductInfo _)) => (declarationTypes env info).flatMap Expr.getUsedConstants
          | some info => if (binderResult info.type).isSort then
              (info.value? (allowOpaque := true)).map Expr.getUsedConstants |>.getD #[]
            else #[]
          | none => #[]
        usesIO (seen.insert name) (used.toList ++ more)

/-- Why a declaration its author wrote is refused, if it is: the first reason. In a proof
library only the reasons that hold there count. -/
def refusal (loaded : Loaded) (written : Written) (inProofs : Bool := false) : MetaM (Option Refusal) := do
  let env := loaded.env
  let name := written.name
  let info := written.info
  let basic : List (Refusal × Bool) := [
    (.isPrivate, isPrivateName name),
    (.isUnsafe, info.isUnsafe),
    (.isAxiom, info matches .axiomInfo _),
    -- An opaque type is how a proof library says it does not care what a thing is.
    (.isPartial, info matches .opaqueInfo _ && !(inProofs && info.type.isSort)),
    (.isMeta, isMetaCode info),
    (.isInstance, isInstanceAnywhere env name),
    (.isNoncomputable, isNoncomputable env name),
    (.doesIO, doesIO env info),
    (.isPolymorphic, !info.levelParams.isEmpty)]
  if let some (why, _) := basic.find? fun (why, holds) => holds && (!inProofs || why.inProofs) then
    return some why
  if inProofs then
    return if ← rests name then some .assumed else none
  let form : Option Refusal := match info with
    | .inductInfo _ =>
      if isClass env name then some .isClass
      else if isStructure env name then (if shape loaded name then none else some .openShape)
      else if closed loaded (.const name []) then none else some .openChoice
    | .defnInfo d =>
      if getReducibilityStatusCore env name != .semireducible then some .isAbbrev
      else definitionForm loaded d
    | .thmInfo rule =>
      if takesType rule.type then some .isPolymorphic
      else if within loaded (operations ++ logic) rule.type then none else some .statement
    | _ => none
  if form.isSome then return form
  if ← rests name then return some .assumed
  match info with
  | .inductInfo _ =>
    if isStructure env name then
      if (getStructureFields env name).isEmpty then return some .singletonChoice
    else if (valuesOf env (mkConst name)).length ≤ 1 && !(← isDecisionError loaded name) then
      return some .singletonChoice
  | .defnInfo d =>
    if let some why ← definitionContentRefusal loaded d then return some why
  | _ => pure ()
  if (← findDocString? env name).isNone then return some .undocumented
  return none

/-- A refusal of one declaration. -/
structure Refused where
  module : Name
  name : Name
  why : Refusal

/-- The names a text links: complete Lean identifiers between backticks. -/
def links (env : Environment) (roots : List Name) (text : String) : List Name :=
  spans ((text.splitOn "`").drop 1)
where
  spans : List String → List Name
    | span :: _ :: more =>
      let input := Parser.mkInputContext span "link"
      let name := (readName env input).filter fun (name, stop) =>
        input.atEnd stop && roots.any (fun root => root != name && root.isPrefixOf name)
      match name with
      | some (name, _) => name :: spans more
      | none => spans more
    | _ => []

/-- Whether a name is a declaration, namespace or module belonging to a configured library. -/
def resolves (loaded : Loaded) (name : Name) : Bool :=
  let all := loaded.modules ++ loaded.proofs
  all.contains name ||
    match loaded.env.find? name with
    | some (.ctorInfo ctor) => loaded.written.any (·.name == ctor.induct)
    | some _ => loaded.written.any (·.name == name)
    | none => loaded.env.isNamespace name && loaded.written.any (name.isPrefixOf ·.name)

/-- Whether a docstring links a name that does not resolve. -/
def dangles (loaded : Loaded) (doc : String) : Bool :=
  (links loaded.env loaded.roots doc).any (!resolves loaded ·)

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
def docRefusal (loaded : Loaded) (doc : String) : Option Refusal :=
  if dangles loaded doc then some .dangling
  else if doc.trimAscii.toString.contains '\n' then some .wordy
  else if dated doc then some .dated
  else none

/-- The type a constant names: a case, a field or a recursor names its type. -/
def namedType (env : Environment) (name : Name) : Name :=
  match env.find? name with
  | some (.ctorInfo ctor) => ctor.induct
  | some (.recInfo _) => name.getPrefix
  | _ =>
    if env.isProjectionFn name || isAuxRecursor env name || isNoConfusion env name then name.getPrefix
    else name

/-- The constants a declaration names in its type, its value and its cases' fields, and
through each constant the compiler made under its name, as a matcher. -/
partial def namedBy (env : Environment) (owner : Name) (info : ConstantInfo) : Std.HashSet Name :=
  walk {} ((declarationTypes env info).flatMap Expr.getUsedConstants ++
    (info.value?.map Expr.getUsedConstants).getD #[]).toList
where
  walk (seen : Std.HashSet Name) : List Name → Std.HashSet Name
    | [] => seen
    | name :: more =>
      if seen.contains name then walk seen more
      else
        let made := match env.find? name with
          | some info => if owner.isPrefixOf name && name != owner then
              info.type.getUsedConstants ++ (info.value?.map Expr.getUsedConstants).getD #[]
            else #[]
          | none => #[]
        walk (seen.insert name) (made.toList ++ more)

/-- The types that a declaration written in the ledger or a proof library uses, beside the
type itself. -/
def usedTypes (loaded : Loaded) : Std.HashSet Name := Id.run do
  let mut used := {}
  for written in loaded.written do
    if !written.standsAlone loaded.env then continue
    for name in namedBy loaded.env written.name written.info do
      let type := namedType loaded.env name
      if type != written.name then used := used.insert type
  return used

/-- Every refusal in the loaded libraries: each declaration of the ledger written in its
source that is outside the forms, each constant the compiler made that the forms do not
allow, each proof that rests on more than Lean's axioms, each `example`, and each
docstring outside its form, a module's too. -/
def refusals (loaded : Loaded) : IO (Array Refused) := do
  let mut found := #[]
  let mut defaults : Std.HashSet Name := {}
  let used := usedTypes loaded
  for written in loaded.written do
    let doc ← findDocString? loaded.env written.name
    let ofLedger := loaded.modules.contains written.module
    -- A case or a field takes the form of its type, and its docstring is its author's call.
    let why ← if written.standsAlone loaded.env then do
        let tactics := defaultTactics loaded.env written.info
        defaults := tactics.foldl (·.insert ·) defaults
        if tactics.any (assumedDefault loaded.env) then pure (some .assumed)
        else loaded.meta (refusal loaded written (inProofs := !ofLedger))
      else pure none
    let why := why.orElse fun _ => doc.bind (docRefusal loaded)
    let why := why.orElse fun _ =>
      if ofLedger && written.standsAlone loaded.env && written.info matches .inductInfo _ &&
        !used.contains written.name then some .unusedType else none
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
      if isMetaCode info && !defaults.contains name then pure (some .isMeta)
      -- What `deriving` makes for a type of the ledger: only `DecidableEq`.
      else if !name.isInternal && isInstanceAnywhere loaded.env name && !ofLedger then pure (some .isInstance)
      else if ← loaded.meta (rests name) then pure (some .assumed)
      else pure none
    if let some why := why then
      found := found.push { module, name := privateToUserName name, why }
  for (module, pos) in loaded.examples do
    if !loaded.modules.contains module then continue
    found := found.push { module, name := Name.mkSimple s!"example at line {pos.line}", why := .isExample }
  for module in loaded.modules ++ loaded.proofs do
    let docs := (getModuleDoc? loaded.env module).map (·.toList.map (·.doc)) |>.getD []
    if docs.any (dangles loaded) then
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

/-- Complete Lean names in text, including names surrounded by quotes at an identifier boundary. -/
def namesIn (env : Environment) (roots : List Name) (text : String) : Array Name := Id.run do
  let input := Parser.mkInputContext text "scope"
  let mut pos := 0
  let mut previous := ' '
  let mut found := #[]
  while !input.atEnd pos do
    let c := input.get pos
    let quoted := c == '\'' && !isIdRest previous
    if quoted || ((isIdFirst c || isIdBeginEscape c) && !isIdRest previous && previous != '.') then
      let start := if quoted then input.next pos else pos
      if let some (name, stop) := readName env input start then
        let last := (stop.prev text).get text
        let name := match name with
          | .str pre part => if quoted && last == '\'' then pre.str (part.dropEnd 1).toString else name
          | _ => name
        if roots.any (fun root => root != name && root.isPrefixOf name) then
          found := found.push name
        previous := last
        pos := stop
        continue
    previous := c
    pos := input.next pos
  return found

/-- The first line of Rust output identifies generated files during a scope scan. -/
def rustBanner : String :=
  "// Generated by the ledger's `emit rust`. Rust literals by their full Lean names."

/-- Each full name under a configured root in tracked files, with its path and line. Git
selects the candidate lines and Lean reads the names. -/
def mentions (loaded : Loaded) (paths : Array String) (backticked : Bool := true) :
    IO (Array (String × Name)) := do
  if loaded.roots.isEmpty then return #[]
  let top ← IO.Process.output { cmd := "git", args := #["rev-parse", "--show-toplevel"] }
  if top.exitCode != 0 then
    throw <| IO.userError s!"git rev-parse: {top.stderr.trimAscii}"
  let patterns := loaded.roots.toArray.flatMap fun root =>
    #["-e", root.getRoot.toString]
  let patterns := if backticked then patterns else patterns ++ #["-e", rustBanner]
  let grep ← IO.Process.output {
    cmd := "git", cwd := top.stdout.trimAscii.toString,
    args := #["grep", "-n", "-I", "-z", "-F"] ++ patterns ++ #["--"] ++ paths }
  -- `git grep` exits 1 when nothing matches, and above 1 when it could not search.
  if grep.exitCode > 1 then
    throw <| IO.userError s!"git grep: {grep.stderr.trimAscii}"
  let lines := (grep.stdout.splitOn "\n").filterMap fun line =>
    match line.splitOn "\x00" with
    | [file, number, text] => some (file, number, text)
    | _ => none
  let generated : Std.HashSet String := if backticked then {} else
    lines.foldl (fun files (file, number, text) =>
      if number == "1" && text.trimAsciiEnd == rustBanner.toSlice then files.insert file else files) {}
  return lines.toArray.flatMap fun (file, number, text) =>
    if generated.contains file then #[] else
      let names := if backticked then (links loaded.env loaded.roots text).toArray
        else namesIn loaded.env loaded.roots text
      names.map (s!"{file}:{number}", ·)

/-- The mentions under `paths` whose name does not resolve. -/
def dangling (loaded : Loaded) (paths : Array String) : IO (Array (String × Name)) :=
  return (← mentions loaded paths).filter fun (_, name) => !resolves loaded name

/-- A part of the ledger or of a proof library, by the prefix of its modules, and the paths
of the repository whose files hold it, relative to the repository's top. The `emit rust`
output names every constant it exports, so the scan skips files with its banner. -/
structure Scope where
  rules : Name
  code : List String

/-- Git treats an empty list and a list of exclusions as starting from every file. -/
private def positivePathspec (path : String) : Bool :=
  if path.isEmpty || path == ":" then false
  else if path.startsWith ":(" then
    match (path.drop 2).toString.splitOn ")" with
    | magic :: _ :: _ => !(magic.splitOn ",").contains "exclude"
    | _ => false
  else if path.startsWith ":" then
    let magic := (path.drop 1).toString.toList.takeWhile (fun c => c ∈ ['!', '^', '/'])
    !magic.any (fun c => c == '!' || c == '^')
  else true

/-- What a declaration is stated in: its type and body, or the fields of its cases; a case
stands for its type. -/
def statedIn (env : Environment) (info : ConstantInfo) : Array Name :=
  let used : Array Name := match info with
    | .thmInfo rule => rule.type.getUsedConstants
    | .inductInfo type => type.ctors.toArray.flatMap fun ctor =>
        ((env.find? ctor).map fun (c : ConstantInfo) => c.type.getUsedConstants).getD #[]
    | other => other.type.getUsedConstants ++ (other.value?.map Expr.getUsedConstants).getD #[]
  used.map fun name => match env.find? name with
    | some (.ctorInfo ctor) => ctor.induct
    | _ => name

/-- The declarations of a scope that no file under its paths holds. A file holds what it
names and what that is stated in; a rule only by its name. A case, a field, an instance and
what the compiler made belong to their declaration. -/
def unheld (loaded : Loaded) (scope : Scope) : IO (Array Written) := do
  if !scope.code.any positivePathspec then
    throw <| IO.userError s!"the scope {scope.rules} needs a positive code pathspec"
  let env := loaded.env
  let mut held : Std.HashSet Name := {}
  let mut todo := ((← mentions loaded scope.code.toArray (backticked := false)).map (·.2)).toList
  repeat
    let name :: rest := todo | break
    todo := rest
    if held.contains name then continue
    held := held.insert name
    let some info := env.find? name | continue
    let further := (statedIn env info).filter fun used =>
      (moduleOf env used).any (loaded.modules ++ loaded.proofs).contains &&
      !(env.find? used matches some (.thmInfo _))
    todo := further.toList ++ todo
  return loaded.written.filter fun w =>
    scope.rules.isPrefixOf w.module && !held.contains w.name &&
    !isPrivateName w.name && w.standsAlone env &&
    !isInstanceAnywhere env w.name

/-- What a project checks: its ledger, the proof libraries beside it, the scopes that tie them
to the code, and the paths of the repository whose links are not the project's, relative to
the repository's top. -/
structure Config where
  ledger : Name
  proofs : List Name := []
  scopes : List Scope := []
  unscanned : List String := []

/-- Loads a project's libraries. -/
def Config.load (config : Config) : IO Loaded := do
  let proofs ← config.proofs.toArray.flatMapM modulesOf
  TeslaValve.load (← modulesOf config.ledger) proofs (config.ledger :: config.proofs)

/-- Checks the ledger: every declaration in its forms, every proof on Lean's axioms alone,
every link to either resolves, in every tracked file of the repository, and every scope's
declarations are held by its code. -/
def check (config : Config) : IO UInt32 := do
  let loaded ← config.load
  -- A project may start from its proofs, before its ledger has a module.
  if loaded.modules.isEmpty && config.proofs.isEmpty then
    IO.eprintln s!"{config.ledger}: no ledger or proof module was found"
    return 1
  let inventory ← proofAxioms loaded loaded.proofs
  let emptyProofs := emptyProofLibraries config.proofs inventory
  for root in emptyProofs do
    IO.eprintln s!"error: the proof library {root} contributes no theorem. Write a theorem there or remove the library from the proof configuration"
  let refused ← refusals loaded
  for r in refused do
    IO.eprintln s!"error: {r.module}: {r.name} {r.why.says}"
  let unscanned := config.unscanned.toArray.map (s!":!{·}")
  let unresolved ← dangling loaded (#["."] ++ unscanned)
  for (place, name) in unresolved do
    IO.eprintln s!"error: {place}: links `{name}`, which neither the ledger nor a proof library declares"
  let all := loaded.modules ++ loaded.proofs
  let mut owed := 0
  for scope in config.scopes do
    if !all.any scope.rules.isPrefixOf then
      IO.eprintln s!"error: the scope {scope.rules} has no module of the ledger or a proof library under it"
      owed := owed + 1
    for w in ← unheld loaded scope do
      IO.eprintln s!"error: {w.module}: {privateToUserName w.name} is named by no file under {scope.code}"
      owed := owed + 1
  if !config.scopes.isEmpty then
    for module in loaded.modules do
      if !config.scopes.any (·.rules.isPrefixOf module) then
        IO.println s!"{module}: no scope lists it, so no code owes its declarations"
  if emptyProofs.isEmpty && refused.isEmpty && unresolved.isEmpty && owed == 0 then
    let proofs := if loaded.proofs.isEmpty then "" else s!", beside {loaded.proofs.size} proof modules"
    let holders := if config.scopes.isEmpty then "" else s!", held by the code of {config.scopes.length} scopes"
    IO.println s!"{config.ledger}: {loaded.written.size} declarations in {loaded.modules.size} modules{proofs}, each in its form{holders}"
    if !inventory.isEmpty then IO.println (proofReport inventory)
    return 0
  return 1

end TeslaValve
