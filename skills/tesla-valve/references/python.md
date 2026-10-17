# Python

Python is soft ground. Its types are hints that nothing checks while the code
runs, so they hold only where a checker runs first, in strict mode. At runtime
the only walls are the ones the code builds itself: a constructor that refuses,
and a parser at the spring.

| wrong shape | right shape | enforcer | not when |
| --- | --- | --- | --- |
| a closed choice as `str`, compared to literals | one class per variant, or an `Enum`, matched case by case, with `case _: assert_never(x)` | pyright strict (`reportMatchNotExhaustive`), or mypy with `exhaustive-match` | the set is owned elsewhere and can grow: parse it at the spring, and refuse what you do not know |
| a positional `bool` parameter, called as `shipping_days(True)` | an `Enum` whose members name the choice | ruff `FBT` | one two-valued choice: make it keyword-only, after `*`, so the call names it |
| an optional attribute that must be set in one state | the variant's class carries it | the checker; pydantic at runtime | the attribute is optional in every state |
| several `bool` attributes that together encode one state: `paid`, `shipped`, `cancelled` | one class per state, or an `Enum` | review: no linter counts them | the bools are truly independent |
| an `int` with no bounds, so a date can run past the calendar | `Field(ge=..., le=...)` for the range the domain allows | pydantic, at the spring and in the constructor | never |
| a class and a `validate()` to call after building it | the constructor refuses, with the reason; `frozen=True` | the constructor itself, at runtime | a value with no invariant stays a primitive |
| `json.loads(raw)`, then `data["status"] == ...` | parse into the domain type at the spring, with a pydantic model in `strict` mode | the model is the check | the data is internal and already typed |
| `model_copy(update=...)` on a model with an invariant | build a new one, so the model checks it | review: `model_copy` does not validate the update | never |
| `cast(T, x)`, `Any`, a blank `# type: ignore` | parse it, or narrow it with `isinstance` | ruff: `TID251` bans `typing.cast`, `ANN401`, `PGH003` | a library's types are wrong: an ignore for one rule, with the reason |
| the clock read inside the logic | read it at the spring and pass the date in | ruff `TID251` bans `datetime.datetime.now`, `.utcnow`, `.today`, `datetime.date.today`, `time.time` | the one function that reads it, under `# noqa: TID251` with the reason |

No tool refuses a `case _:` that quietly returns a value. The only catch-all
that belongs in a `match` is `case _: assert_never(x)`, which is a proof, not a
catch-all. Holding that line is review.

## A closed choice, parsed at the spring

The discriminated union is the check: an unknown status is refused with "does
not match any of the expected tags", and a backorder without its days or with a
count out of range is refused too. `frozen=True` leaves no setter, and
`strict=True` refuses what lax mode would quietly convert: JSON `true`, `3.0`
and `"3"` would all become `3`. The range keeps the sum inside the calendar.

<!-- code: examples/python/shop/delivery.py#stock -->
```python
class InStock(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)
    status: Literal["in_stock"] = "in_stock"


class Backorder(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)
    status: Literal["backorder"] = "backorder"
    restock_days: Annotated[int, Field(ge=0, le=65535)]


Stock = Annotated[InStock | Backorder, Field(discriminator="status")]
stock_of = TypeAdapter(Stock).validate_json


def delivery_date(postcode: Postcode, stock: Stock, today: date) -> date:
    match stock:
        case InStock():
            days = shipping_days(postcode)
        case Backorder(restock_days=restock_days):
            days = restock_days + shipping_days(postcode)
        case _:
            assert_never(stock)
    return today + timedelta(days=days)
```

## One constructor

Python has no private constructor, so the constructor itself is the gate:

<!-- code: examples/python/shop/postcode.py#postcode -->
```python
@dataclass(frozen=True)
class Postcode:
    code: str

    def __post_init__(self) -> None:
        if not (len(self.code) == 5 and self.code.isascii() and self.code.isdigit()):
            raise Invalid("a postcode is five digits")
```

`isascii()` matters: `isdigit()` alone accepts full-width digits.

## The holes

`object.__setattr__` writes through `frozen=True`, `Postcode.__new__` skips
`__post_init__`, and pydantic's `model_construct` and
`model_copy(update=...)` skip the model's checks. No tool refuses them. Each
one is a deliberate act everyone can see in review, which is the most soft
ground offers.

Where untyped code calls in, the annotations are no wall. Validate the
arguments where they enter, with `@validate_call` or a model; neither re-checks
a model that was built past its checks.

## The clock

ruff refuses the clock everywhere but in the one function that reads it, which
says why it may:

<!-- code: examples/python/shop/clock.py#clock -->
```python
def today() -> date:
    """The clock is a spring: read it here, once, and pass the date in."""
    return date.today()  # noqa: TID251 # the one place that reads the clock
```

The
[Python example](https://github.com/Aquilo-Solution-S/tesla-valve/tree/main/examples/python)
runs every enforcer above, and each is fed a file it must refuse.
