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
| the same audit, on the code | the code of a scope holds every declaration in the modules the scope lists, and every name the code cites is declared | the same program |

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
needs the library, so `lake exe audit` never reads a build that is older
than the source:

<!-- code: examples/lean/lakefile.toml#audit -->
```toml
# The gate's own program. It is not part of the model, so it may do IO. It reads
# what the build produced, so the spec is built before it runs.
[[lean_exe]]
name = "audit"
root = "Audit"
needs = ["Spec"]
supportInterpreter = true
```

It reads the modules from the tree, loads what the build produced, and
refuses a declaration of the spec for one of five reasons:

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

The same program ties the spec to the code. The code names the declaration
it holds with `@holds <name>`, and the scopes at the top of the audit say
which code holds which modules, as the tesla-valve skill's
[Lean reference](../../tesla-valve/references/lean.md#one-part-of-the-spec-at-a-time)
shows. Add a scope for each module the code already holds. With no scope
this row of the table is off: report it so, and prove it with the first
scope. The paths are read from the directory `lake` runs in. List the
directories of the source, not a build output: a compiled file can carry a
name its source no longer has.

The whole program is in
[the example](https://github.com/Aquilo-Solution-S/tesla-valve/blob/main/examples/lean/Audit.lean).
Copy it, change `Spec` to the name of the project's library, and write the
project's own scopes.

## CI

```sh
lake build --wfail
lake exe audit
```

Where a program beside the model writes a file the code reads, as the vectors
a test replays, run it after these and fail on a difference:

```sh
lake exe vectors
git diff --exit-code
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

In a module a scope lists, it refuses a declaration no code names. The bad
file goes under the scope, which its `slot:` line says:

<!-- code: examples/bad/lean/unnamed.lean -->
```lean
-- slot: Spec/Stock/Rush.lean
-- expect: no code under [../python/shop, ../python/tests] names in_stock_takes_shipping_only
import Spec.Stock

/-- An item in stock takes the shipping time and no more. -/
theorem in_stock_takes_shipping_only (shipping : Nat) : deliveryDays shipping .inStock = shipping :=
  rfl
```

And it refuses a name in the code that the spec does not declare. This bad
file goes into the code:

<!-- code: examples/bad/lean/stale.py -->
```python
# slot: ../python/tests/test_rush.py
# expect: names rush_ships_today, which the spec does not declare
def test_a_rush_order_ships_today() -> None:
    """@holds rush_ships_today"""
```

It refuses a model that acts instead of deciding, behind an alias too:

<!-- code: examples/bad/lean/io_in_the_model.lean -->
```lean
-- expect: Effect does IO
abbrev Effect := IO

def announce : Effect Unit := IO.println "shipped"
```
