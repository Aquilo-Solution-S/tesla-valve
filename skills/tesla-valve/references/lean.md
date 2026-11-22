# Lean

Give each rule a home the gate can read. A ledger in Lean holds the rules
its forms can express. The compiler checks the proofs. The ledger tool checks
the forms and the ties to code, draws the ledger, and gives the code values
and test vectors.

## The forms

| Form | Lean |
| --- | --- |
| Closed choice | An `inductive` whose cases carry nothing or other closed choices. |
| Shape | A `structure` of ledger values, with any invariant as an `ok : decision fields = true` field. |
| Constant | A `def` of a ledger value. |
| Decision | A `def` that matches its closed inputs case by case into ledger values. |
| State machine | A decision from state and event to state, or to `Except Refusal State`. The event is a closed choice of its own. |
| Theorem | A proved rule about the ledger. |
| Rejected design | A theorem named `not_…` that shows which rule an alternative breaks. |

At each match on a closed choice, name the constructor in every alternative.
An or-pattern can share a body across explicitly named constructors. A
constructor pattern can bind fields for use in the body or in a nested match.

A ledger value is a closed choice, a shape, a `Nat`, a `Bool`, a `String`,
a `List` or `Option` of a value, or an `Except` with a closed refusal
choice and a value. An `Option` cannot directly contain another `Option`.
Use strings for exact keys or other values a system reads. Give a rule its
own declaration.

Each ledger declaration has a one-line docstring. Give a case or field one
where its name leaves out a condition or a bound. Give a module its title in
its module docstring. Git and the tracker keep dates and the story.

<!-- code: examples/lean/Shop/Shipping.lean#shipping -->
```lean
namespace Shop.Shipping

/-- The two shipping speeds the shop offers. -/
inductive Speed where
  | local
  | standard

/-- Postcodes in the local delivery area start with this prefix. -/
def localPrefix : String := "1"

/-- Days for local shipping. -/
def localDays : Nat := 2

/-- Days for standard shipping. -/
def standardDays : Nat := 3

/-- Days in transit for each speed. -/
def shippingDays : Speed → Nat
  | .local => localDays
  | .standard => standardDays

/-- Local shipping takes fewer days than standard shipping. -/
theorem local_shipping_is_faster : shippingDays .local < shippingDays .standard := by
  decide

end Shop.Shipping
```

## Proof libraries

Keep a rule that needs arithmetic, recursion or induction in a proof library.
Its types and definitions can use ordinary Lean. The gate checks its proofs
and the docstrings it has. It refuses `unsafe`, `axiom`, `partial`,
`noncomputable`, IO, and proofs that depend on `sorry`, `native_decide` or
an axiom beyond Lean's own. A proof library may use an opaque type to leave
its representation unspecified. An outside fact goes in the hypotheses of
the theorem that uses it. The gate inspects retained default tactics for
`sorry`, `admit` and `native_decide`. Lean discards proof-library `example`
bodies after elaboration, so use `lake build --wfail` to catch their proof
warnings.

A backorder carries a natural number and adds it to the shipping time. The
shop keeps that decision and its proofs in `Spec.Stock`.

<!-- code: examples/lean/Spec/Stock.lean#stock -->
```lean
namespace Spec

/-- What the warehouse says about an item. -/
inductive Stock where
  | inStock
  | backorder (restockDays : Nat)

/-- Days until the parcel arrives. -/
def deliveryDays (shipping : Nat) : Stock → Nat
  | .inStock => shipping
  | .backorder restockDays => restockDays + shipping

/-- A backorder never arrives before the same item in stock. -/
theorem backorder_not_sooner (shipping restockDays : Nat) :
    deliveryDays shipping .inStock ≤ deliveryDays shipping (.backorder restockDays) := by
  simp [deliveryDays]

/-- One delivery promise would give a backorder the date of an item in stock. -/
theorem not_one_promise : ∃ shipping restockDays,
    deliveryDays shipping (.backorder restockDays) ≠ deliveryDays shipping .inStock :=
  ⟨0, 1, by decide⟩

#guard deliveryDays 2 (.backorder 3) == 5

end Spec
```

`check` guards against mistakes in trusted source. It relies on Lean's
declaration ranges and authored name prefixes to identify generated declarations,
and on kernel checking for proofs. Source that tampers with that metadata or
sets `debug.skipKernelTC` is outside that guarantee.

## Links and scopes

Link a rule by its full Lean name in backticks beside the code or test that
holds it. A link that starts with a library root must resolve to a
declaration, module or namespace in a configured library in every tracked
file the check scans. A namespace counts when it contains a declaration of
that library. The checker refuses links to compiler-generated names. A root
module is checked alongside its submodules.
The same syntax works in a docstring.

<!-- code: examples/python/tests/test_shop.py#named -->
```python
def test_a_backorder_never_arrives_sooner() -> None:
    """`Spec.backorder_not_sooner`"""
    in_stock = delivery_date(Postcode("10115"), InStock(), date(2026, 10, 6))
    for restock_days in (0, 1, 30):
        backorder = Backorder(restock_days=restock_days)
        assert delivery_date(Postcode("10115"), backorder, date(2026, 10, 6)) >= in_stock
```

A scope names a prefix of modules and the repository paths whose code
holds them. Every declaration in the scope must be named there by its full
name, or be stated in a declaration that is. Constructors and fields
belong to their type. A theorem counts only when
the code names the theorem itself. A decision that names a type in its
statement or body holds the type too. A full name in code counts for a
scope without backticks, as it does inside `ledger!`. A longer name
that contains the full name does not satisfy the scope.

Each scope is checked on its own. The shop has four scopes for `Spec.Stock`,
one for each language. A module outside the scopes still passes the Lean
checks. Add a scope as soon as its code holds the declarations. Each scope
needs a positive Git pathspec. The scope scan skips files with the `emit rust`
banner, since those files name every constant they export.

## What the ledger gives the code

`lake exe shop emit rust` prints a `ledger!` macro. It exports `Nat`,
`Bool`, `String`, and `List` and `Option` whose element types also have Rust
literals. A list becomes an array. Nested lists and a `Nat` above `u128::MAX`
fail emission.
The Rust consumer owns the representation of closed choices, shapes and
`Except` values, and links those constants by their Lean names. A ledger
with no Rust literals still emits a macro. Exported names use dotted ASCII
identifier tokens, including leading underscores. The compiler refuses an
unknown name. Commit the generated file and have the gate regenerate and
compare it.

<!-- code: examples/rust/src/lib.rs#shipping-days -->
```rust
/// Transit days for a postcode under `Shop.Shipping.shippingDays`.
pub fn shipping_days(postcode: &Postcode) -> u64 {
    const LOCAL_PREFIX: &str = ledger!(Shop.Shipping.localPrefix);
    if postcode.as_str().starts_with(LOCAL_PREFIX) {
        ledger!(Shop.Shipping.localDays)
    } else {
        ledger!(Shop.Shipping.standardDays)
    }
}
```

`lake exe shop emit vectors` prints JSON. Each ledger decision's full name
maps to rows with an `in` array and an `out` value, one for every combination
of inputs. Replay the rows against the code that implements the decision.

- A case is a string, such as `"cancelled"`.
- A case with payload is an object keyed by the case, such as `{"paint":["red"]}`.
- A shape is an object of its fields, omitting the proof field `ok`.
- An `Option` is `null` or the encoded value.
- An `Except` is an object with one key, `ok` or `error`, and its encoded value.

JSON `Nat` values above `2^53` retain their exact digits. A JavaScript reader
must parse them as big integers to preserve their precision.

A proof-library decision can have inputs outside the forms. The shop's
separate `vectors` program chooses inputs for `Spec.deliveryDays`. Each
language's test names and replays that decision.

<!-- code: examples/python/tests/test_shop.py#replayed -->
```python
class Vector(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)
    shipping: int
    stock: Stock
    days: int


# Replay `Spec.deliveryDays` with the inputs encoded by `Spec.stockJson`.
vectors_of = TypeAdapter(list[Vector]).validate_json
VECTORS = vectors_of((Path(__file__).parent / "delivery_days.json").read_bytes())


@pytest.mark.parametrize("postcode", [Postcode("10115"), Postcode("20095")])
def test_the_code_decides_the_days_the_spec_decides(postcode: Postcode) -> None:
    today = date(2026, 10, 6)
    replayed = [vector for vector in VECTORS if vector.shipping == shipping_days(postcode)]
    assert replayed
    for vector in replayed:
        assert delivery_date(postcode, vector.stock, today) == today + timedelta(days=vector.days)
```

`lake exe shop view` prints Markdown from the Lean. It shows the ledger's
shapes, values and decision tables, with theorems beside them. Read the view
when you need the answer to a rule or want to see the whole decision table.

[Set up the gate and run the tool's selftest.](../../prepare/references/lean.md)
