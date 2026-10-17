# Python

| tool | holds | comes with |
| --- | --- | --- |
| pyright, strict, or mypy, strict | every case of a `match`, every argument, every type, before the code runs | a dev dependency |
| ruff | no `cast`, no `Any`, no blanket ignore, no positional `bool`, no clock inside the logic | a dev dependency |
| pydantic | the closed choice and the range at the spring, while the code runs | a dependency of the code |
| pytest | the intent and the springs | a dev dependency |

## The tools

Pyright and mypy both check the annotations, and neither runs with the code.
One is enough: keep the one the project already runs. Pin all of them the way
the project pins the rest, in a requirements file, `uv.lock` or
`poetry.lock`:

<!-- code: examples/python/requirements.txt -->
```text
# The versions CI checks the example with.
pydantic==2.14.0
pyright==1.1.414
mypy==2.4.0
ruff==0.16.10
pytest==9.1.1
```

## The config

In `pyproject.toml`, with pyright for the types and ruff for the leaks:

<!-- code: examples/python/pyproject.toml#enforcers -->
```toml
[tool.pyright]
typeCheckingMode = "strict"
enableTypeIgnoreComments = false

[tool.ruff.lint]
select = ["ANN", "FBT", "PGH", "TID251"]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"typing.cast".msg = "a cast forges a value; parse it at the spring"
"datetime.datetime.now".msg = "read the clock at the spring and pass it in"
"datetime.datetime.utcnow".msg = "read the clock at the spring and pass it in"
"datetime.datetime.today".msg = "read the clock at the spring and pass it in"
"datetime.date.today".msg = "read the clock at the spring and pass it in"
"time.time".msg = "read the clock at the spring and pass it in"
```

Pyright reads any `# type: ignore`, even one with a code, as an ignore for the
whole line. With `enableTypeIgnoreComments = false` it honors only
`# pyright: ignore[rule]`, which ignores that one rule.

`select` replaces ruff's default rules. In a project that relies on them, add
the three with `extend-select` instead.

With mypy instead of pyright, where `# type: ignore[code]` is that narrow:

<!-- code: examples/python/pyproject.toml#mypy -->
```toml
[tool.mypy]
strict = true
warn_unreachable = true
enable_error_code = ["exhaustive-match"]
```

The clock ban finds every place the project reads the clock today. They move
behind one function, the way
[the clock](../../tesla-valve/references/python.md#the-clock) shows.

## CI

```sh
pyright        # or: mypy .
ruff check
pytest
```

## The proofs

Run the type checker and `ruff check` in the copy. Put the bad file inside the
project's package, so its imports resolve. A file with an `expect:` line for
each checker keeps the one for the checker the project runs, and the coded
ignore is a proof only under pyright.

The type checker refuses a missing case and a missing argument:

<!-- code: examples/bad/python/missing_case.py -->
```python
# expect: reportMatchNotExhaustive
# expect: [exhaustive-match]
from shop.delivery import InStock, Stock


def restock_days(stock: Stock) -> int:
    match stock:
        case InStock():
            return 0
```

<!-- code: examples/bad/python/backorder_without_days.py -->
```python
# expect: Argument missing for parameter "restock_days"
from shop.delivery import Backorder


def backorder() -> Backorder:
    return Backorder()
```

Pyright reads past a coded `# type: ignore`:

<!-- code: examples/bad/python/coded_ignore_under_pyright.py -->
```python
# expect: reportAssignmentType
answer: str = 42  # type: ignore[assignment]
```

ruff refuses the leaks, a positional flag and the clock:

<!-- code: examples/bad/python/cast_forges_a_value.py -->
```python
# expect: TID251 `typing.cast` is banned
from typing import cast

from shop.postcode import Postcode


def forged(raw: object) -> Postcode:
    return cast(Postcode, raw)
```

<!-- code: examples/bad/python/any_annotation.py -->
```python
# expect: ANN401
from typing import Any


def passthrough(value: Any) -> Any:
    return value
```

<!-- code: examples/bad/python/blanket_ignore.py -->
```python
# expect: PGH003
answer: str = 42  # type: ignore
```

<!-- code: examples/bad/python/bool_flag.py -->
```python
# expect: FBT001
# expect: FBT003
def shipping_days(express: bool) -> int:
    return 1 if express else 3


def express_days() -> int:
    return shipping_days(True)
```

<!-- code: examples/bad/python/clock_today.py -->
```python
# expect: `datetime.date.today` is banned
from datetime import date


def today() -> date:
    return date.today()
```

<!-- code: examples/bad/python/clock_utcnow.py -->
```python
# expect: `datetime.datetime.utcnow` is banned
from datetime import datetime


def now() -> datetime:
    return datetime.utcnow()
```
