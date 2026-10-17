from datetime import date


# region: clock
def today() -> date:
    """The clock is a spring: read it here, once, and pass the date in."""
    return date.today()  # noqa: TID251 # the one place that reads the clock


# endregion
