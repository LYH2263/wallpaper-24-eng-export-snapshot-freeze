import math


def ceil_units(v: float) -> int:
    return int(math.ceil(float(v) - 1e-9))


def floor_units(v: float) -> int:
    return int(math.floor(float(v) + 1e-9))
