import TeslaValve.View
open Lean

/-! The ledger hands literal constants to Rust as macro arms, and decisions to tests as
vectors with the answer to every input. -/

namespace TeslaValve

/-- The ledger types Rust can spell without a consumer's declarations. -/
partial def rustLiteralType : Expr → Bool
  | .const name [] => name ∈ [``Nat, ``Bool, ``String]
  | .app (.const name [_]) inner => (name ∈ [``List, ``Option]) && rustLiteralType inner
  | _ => false

/-- An array cannot represent lists of different lengths, even through Option. -/
private partial def nestedRustList (type : Expr) (insideList : Bool := false) : Bool :=
  match type with
  | .app (.const ``List _) inner => insideList || nestedRustList inner true
  | .app (.const ``Option _) inner => nestedRustList inner insideList
  | _ => false

/-- Rust string literals use only printable ASCII in the generated source. -/
private def rustString (s : String) : String :=
  "\"" ++ s.foldl (fun out c => out ++
    match c with
    | '\n' => "\\n"
    | '\r' => "\\r"
    | '\t' => "\\t"
    | '\\' => "\\\\"
    | '"' => "\\\""
    | _ =>
      if c.toNat < 0x20 || c.toNat > 0x7e then
        "\\u{" ++ String.ofList (Nat.toDigits 16 c.toNat) ++ "}"
      else String.singleton c) "" ++ "\""

/-- A value of a literal type, with a refusal for a number Rust cannot represent. -/
partial def rustLiteral (e : Expr) : Except String String := do
  let args := e.getAppArgs
  match e.getAppFn with
  | .const ``Bool.true _ => return "true"
  | .const ``Bool.false _ => return "false"
  | .const ``OfNat.ofNat _ => rustLiteral args[1]!
  | .lit (.natVal n) =>
    if n < 2 ^ 128 then return toString n
    else throw s!"Nat {n} exceeds u128::MAX"
  | .lit (.strVal s) => return rustString s
  | .const ``Option.none _ => return "None"
  | .const ``Option.some _ => return s!"Some({← rustLiteral args.back!})"
  | .const ``List.nil _ | .const ``List.cons _ =>
    return s!"[{", ".intercalate (← (← listItems e).mapM rustLiteral)}]"
  | _ => throw s!"{e} did not reduce to a Rust literal"

/-- The Lean name as dotted Rust identifier tokens. -/
def rustSpelling (name : Name) : Option String := do
  let parts ← name.components.mapM fun
    | .str _ s =>
      if (s.front.isAlpha || s.front == '_') && s.all (fun c => c.isAlphanum || c == '_')
        then some s else none
    | _ => none
  return ".".intercalate parts

/-- The Rust literals of the ledger, addressed by their full names in `ledger!`. -/
def emitRust (loaded : Loaded) : IO (Except String String) := do
  let mut arms := #[]
  for w in loaded.written do
    if !loaded.modules.contains w.module || !w.standsAlone loaded.env then continue
    let .defnInfo d := w.info | continue
    if !(rustLiteralType d.type) then continue
    if nestedRustList d.type then
      return .error s!"{w.name}: Rust emission does not support nested lists"
    let some key := rustSpelling w.name | return .error s!"no Rust tokens spell {w.name}"
    let value ← loaded.reduce w.name
    let literal ← match rustLiteral value with
      | .ok literal => pure literal
      | .error why => return .error s!"{w.name}: {why}"
    let doc ← docOf loaded.env w.name
    arms := arms.push s!"    // {doc}\n    ({key}) => \{\n        {literal}\n    };"
  if arms.isEmpty then
    arms := #["    ($($name:tt)*) => { compile_error!(\"the ledger has no Rust literal constants\") };"]
  return .ok s!"{rustBanner}\n#[macro_export]\nmacro_rules! ledger \{\n{"\n".intercalate arms.toList}\n}\n"

/-- A value as JSON: a case by its name, or as an object of its name and what it carries; a
shape as an object of its fields, without its invariant; an `Except` as `ok` or `error`. -/
partial def toJson (env : Environment) (e : Expr) : Except String Json := do
  let args := e.getAppArgs
  match e.getAppFn with
  | .const ``Bool.true _ => return .bool true
  | .const ``Bool.false _ => return .bool false
  | .const ``OfNat.ofNat _ => toJson env args[1]!
  | .lit (.natVal n) => return .num n
  | .lit (.strVal s) => return .str s
  | .const ``Option.none _ => return .null
  | .const ``Option.some _ => toJson env args.back!
  | .const ``Except.ok _ => return .mkObj [("ok", ← toJson env args.back!)]
  | .const ``Except.error _ => return .mkObj [("error", ← toJson env args.back!)]
  | .const ``List.nil _ | .const ``List.cons _ =>
    return .arr (← (← listItems e).mapM (toJson env)).toArray
  | .const ctor _ => match env.find? ctor with
    | some (.ctorInfo info) =>
      let fields := args.extract info.numParams args.size
      let case := match ctor with | .str _ s => s | _ => ctor.toString
      if isStructure env info.induct then
        return .mkObj (← (shapeFields env info fields).mapM fun (field, v) =>
          return (field.toString, ← toJson env v))
      else if fields.isEmpty then return .str case
      else return .mkObj [(case, .arr (← fields.mapM (toJson env)))]
    | _ => throw s!"{e} did not reduce to a ledger value"
  | _ => throw s!"{e} did not reduce to a ledger value"

/-- Every decision of the ledger, by its full name, with its answer to each of its inputs. -/
def emitVectors (loaded : Loaded) : IO Json := do
  let mut decisions := #[]
  for w in loaded.written do
    if !loaded.modules.contains w.module then continue
    let some inputs := w.decisionInputs loaded | continue
    let mut rows := #[]
    for combination in combinations loaded.env inputs do
      let answer ← loaded.reduce w.name combination.toArray
      let (inputs, output) ← computed w.name do
        return ((← combination.mapM (toJson loaded.env)).toArray, ← toJson loaded.env answer)
      rows := rows.push (Json.mkObj [
        ("in", .arr inputs), ("out", output)])
    decisions := decisions.push (w.name.toString, Json.arr rows)
  return .mkObj decisions.toList

/-- Prints what `emit rust` or `emit vectors` hands to the code. -/
def emit (config : Config) (target : String) : IO UInt32 := do
  let loaded ← config.load
  match target with
  | "rust" =>
    match ← emitRust loaded with
    | .ok text => IO.print text; return 0
    | .error why => IO.eprintln s!"error: {why}"; return 1
  | "vectors" => IO.println (← emitVectors loaded).pretty; return 0
  | _ => IO.eprintln s!"error: emit {target}: what it emits is rust or vectors"; return 2

end TeslaValve
