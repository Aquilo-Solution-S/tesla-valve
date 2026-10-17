# expect: FBT001
# expect: FBT003
def shipping_days(express: bool) -> int:
    return 1 if express else 3


def express_days() -> int:
    return shipping_days(True)
