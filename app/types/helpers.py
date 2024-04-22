from typing import NamedTuple

IMAGE_DTYPES = [
    "bool",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "int16",
    "int32",
    "int64",
    "float32",
    "float64",
]


class BoundingBox(NamedTuple):
    min_x: float
    min_y: float
    max_x: float
    max_y: float


class TimeRange(NamedTuple):
    start: str
    end: str


class HeightWidth(NamedTuple):
    height: int
    width: int
