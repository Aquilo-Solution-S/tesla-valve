# expect: `datetime.datetime.utcnow` is banned
from datetime import datetime


def now() -> datetime:
    return datetime.utcnow()
