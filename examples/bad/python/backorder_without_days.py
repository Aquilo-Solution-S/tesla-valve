# expect: Argument missing for parameter "restock_days"
from shop.delivery import Backorder


def backorder() -> Backorder:
    return Backorder()
