from dataclasses import dataclass


class Invalid(ValueError):
    pass


# region: postcode
@dataclass(frozen=True)
class Postcode:
    code: str

    def __post_init__(self) -> None:
        if not (len(self.code) == 5 and self.code.isascii() and self.code.isdigit()):
            raise Invalid("a postcode is five digits")


# endregion
