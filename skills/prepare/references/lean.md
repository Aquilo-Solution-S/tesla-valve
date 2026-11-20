# Lean

A spec in Lean is a project of its own beside the code, built by the same
gate. What it may contain is in the tesla-valve skill's
[Lean reference](../../tesla-valve/references/lean.md).

| tool | holds | comes with |
| --- | --- | --- |
| the compiler | every proof, every `#guard` and `example`, every match | the toolchain |
| `lake build --wfail` | no `sorry`: its warning fails the build | the toolchain |
| the `Spec.+` glob | every module of the spec is built, imported or not | Lake |
| an audit of the built spec | no `axiom`, `partial`, `unsafe`, `noncomputable` or `IO` in the model | a small program beside the spec |

## The tools

Pin the toolchain in `lean-toolchain`. `elan` reads the file, and every `lake`
call below it uses that toolchain:

<!-- code: examples/lean/lean-toolchain -->
```text
leanprover/lean4:v4.35.0
```

Commit `lake-manifest.json`.

## The config

In `lakefile.toml`, the library is a glob, not a root module that imports the
rest. A root module is a list each new file must be added to, and a file left
out of it is never checked:

<!-- code: examples/lean/lakefile.toml#whole-spec -->
```toml
# Every module under Spec/ is built, whether or not anything imports it.
[[lean_lib]]
name = "Spec"
globs = ["Spec.+"]
```

The audit is an executable in the same package and outside the model. It
reads the modules from the tree, loads what the build produced, and refuses a
declaration of the spec for one of five reasons:

<!-- code: examples/lean/Audit.lean#refusal -->
```lean
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
```

The whole program is in
[the example](https://github.com/Aquilo-Solution-S/tesla-valve/blob/main/examples/lean/Audit.lean).
Copy it, and change `Spec` to the name of the project's library.

## CI

```sh
lake build --wfail
lake exe audit
```

## The proofs

Put the bad file in the spec as a module nothing imports, such as
`Spec/Bad.lean`, and run both commands in the copy.

The build refuses an assumed proof, and a false one in a module nothing
imports:

<!-- code: examples/bad/lean/sorry.lean -->
```lean
-- expect: declaration uses `sorry`
theorem restock_is_short (restockDays : Nat) : restockDays ≤ 14 := by sorry
```

<!-- code: examples/bad/lean/not_imported.lean -->
```lean
-- expect: Tactic `decide` proved that the proposition
-- Nothing imports this module, and the gate still builds it.
example : 2 + 2 = 5 := by decide
```

The audit refuses an outside fact declared as an axiom, private or not. It
belongs in the hypotheses of the theorem that needs it:

<!-- code: examples/bad/lean/axiom.lean -->
```lean
-- expect: warehouse_is_honest is an axiom
private axiom warehouse_is_honest (restockDays : Nat) : restockDays ≤ 14
```

It refuses a decision that need not terminate, one that steps outside the
kernel, and one that cannot be evaluated:

<!-- code: examples/bad/lean/partial.lean -->
```lean
-- expect: retry is partial or opaque
partial def retry (attempt : Nat) : Nat := retry (attempt + 1)
```

<!-- code: examples/bad/lean/unsafe.lean -->
```lean
-- expect: forgedDays is unsafe
unsafe def forgedDays (raw : Nat) : Nat := raw
```

<!-- code: examples/bad/lean/noncomputable.lean -->
```lean
-- expect: someDays is noncomputable
noncomputable def someDays : Nat := Classical.choice ⟨0⟩
```

And it refuses a model that acts instead of deciding, behind an alias too:

<!-- code: examples/bad/lean/io_in_the_model.lean -->
```lean
-- expect: Effect does IO
abbrev Effect := IO

def announce : Effect Unit := IO.println "shipped"
```
