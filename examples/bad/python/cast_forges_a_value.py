# expect: TID251 `typing.cast` is banned
from typing import cast

from shop.postcode import Postcode


def forged(raw: object) -> Postcode:
    return cast(Postcode, raw)
