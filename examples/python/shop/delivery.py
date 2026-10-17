from datetime import date, timedelta
from typing import Annotated, Literal, assert_never

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from shop.postcode import Postcode


# region: stock
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


# endregion


def shipping_days(postcode: Postcode) -> int:
    return 2 if postcode.code.startswith("1") else 3
