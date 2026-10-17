from datetime import date

import pytest
from pydantic import ValidationError

from shop.delivery import Backorder, InStock, delivery_date, stock_of
from shop.postcode import Invalid, Postcode


def test_ordered_on_tuesday_arrives_on_thursday() -> None:
    arrives = delivery_date(Postcode("10115"), InStock(), date(2026, 10, 6))
    assert arrives == date(2026, 10, 8)


def test_a_backorder_ships_once_restocked() -> None:
    arrives = delivery_date(Postcode("10115"), Backorder(restock_days=5), date(2026, 10, 6))
    assert arrives == date(2026, 10, 13)


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
