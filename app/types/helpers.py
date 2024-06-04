import datetime
import enum
from typing import NamedTuple, Optional, Union

from pydantic import BaseModel


class SCL(enum.IntEnum):
    NO_DATA = 0
    SATURATED = 1
    SHADOWS = 2
    CLOUD_SHADOWS = 3
    VEGETATION = 4
    NOT_VEGETATED = 5
    WATER = 6
    UNCLASSIFIED = 7
    CLOUD_MEDIUM_PROB = 8
    CLOUD_HIGH_PROB = 9
    THIN_CIRRUS = 10
    SNOW_ICE = 11

    @classmethod
    def is_valid(cls, value):
        return value in cls.__members__.values()


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
    start: datetime.datetime
    end: datetime.datetime


class HeightWidth(NamedTuple):
    height: int
    width: int


class Geometry(BaseModel):
    type: str
    coordinates: list


class Feature(BaseModel):
    type: str
    geometry: Geometry
    properties: Optional[dict]


class FeatureCollection(BaseModel):
    type: str
    features: list[Feature]


GeoJSON = Union[Geometry, Feature, FeatureCollection]


class PolygonGeometry(Geometry):
    type: str = "Polygon"
    coordinates: list[list[list[float]]]


class PolygonFeature(Feature):
    geometry: PolygonGeometry


class PolygonFeatureCollection(FeatureCollection):
    features: list[PolygonFeature]


PolygonGeoJSON = Union[PolygonGeometry, PolygonFeature, PolygonFeatureCollection]
