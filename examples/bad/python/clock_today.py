# expect: `datetime.date.today` is banned
from datetime import date


def today() -> date:
    return date.today()
