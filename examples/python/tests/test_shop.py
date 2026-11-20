from datetime import date, timedelta
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from shop.delivery import Backorder, InStock, Stock, delivery_date, shipping_days, stock_of
from shop.postcode import Invalid, Postcode


def test_ordered_on_tuesday_arrives_on_thursday() -> None:
    arrives = delivery_date(Postcode("10115"), InStock(), date(2026, 10, 6))
    assert arrives == date(2026, 10, 8)


def test_a_backorder_ships_once_restocked() -> None:
    arrives = delivery_date(Postcode("10115"), Backorder(restock_days=5), date(2026, 10, 6))
    assert arrives == date(2026, 10, 13)


# region: named
def test_a_backorder_never_arrives_sooner() -> None:
    """@holds backorder_not_sooner"""
    in_stock = delivery_date(Postcode("10115"), InStock(), date(2026, 10, 6))
    for restock_days in (0, 1, 30):
        backorder = Backorder(restock_days=restock_days)
        assert delivery_date(Postcode("10115"), backorder, date(2026, 10, 6)) >= in_stock


# endregion


def test_a_backorder_is_not_promised_the_date_of_an_item_in_stock() -> None:
    """@holds not_one_promise"""
    in_stock = delivery_date(Postcode("10115"), InStock(), date(2026, 10, 6))
    assert delivery_date(Postcode("10115"), Backorder(restock_days=1), date(2026, 10, 6)) != in_stock


# region: replayed
class Vector(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)
    shipping: int
    stock: Stock
    days: int


# @holds Vectors: `lake exe vectors`, in examples/lean, writes this file.
vectors_of = TypeAdapter(list[Vector]).validate_json
VECTORS = vectors_of((Path(__file__).parent / "delivery_days.json").read_bytes())


@pytest.mark.parametrize("postcode", [Postcode("10115"), Postcode("20095")])
def test_the_code_decides_the_days_the_spec_decides(postcode: Postcode) -> None:
    today = date(2026, 10, 6)
    replayed = [vector for vector in VECTORS if vector.shipping == shipping_days(postcode)]
    assert replayed
    for vector in replayed:
        assert delivery_date(postcode, vector.stock, today) == today + timedelta(days=vector.days)


# endregion


@pytest.mark.parametrize(
    "raw",
    [
        '{"status": "discontinued"}',
        '{"status": "backorder"}',
        '{"status": "backorder", "restock_days": -3}',
        '{"status": "backorder", "restock_days": 70000}',
        '{"status": "backorder", "restock_days": true}',
        '{"status": "backorder", "restock_days": "3"}',
    ],
)
def test_the_warehouse_spring_refuses_what_it_does_not_know(raw: str) -> None:
    with pytest.raises(ValidationError):
        stock_of(raw)


@pytest.mark.parametrize("raw", ["1011", "101155", "1011a", "１０１１５"])
def test_the_checkout_spring_refuses_what_is_not_a_postcode(raw: str) -> None:
    with pytest.raises(Invalid):
        Postcode(raw)
