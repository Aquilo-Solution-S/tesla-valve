# expect: reportMatchNotExhaustive
# expect: [exhaustive-match]
from shop.delivery import InStock, Stock


def restock_days(stock: Stock) -> int:
    match stock:
        case InStock():
            return 0
