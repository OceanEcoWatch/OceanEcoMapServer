

import datetime
from geoalchemy2 import Geometry, Raster, RasterElement
from geoalchemy2.types import WKBElement
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,   
)
from sqlalchemy.orm import declarative_base, relationship
Base = declarative_base()

class PredictionVector(Base):
    __tablename__ = "prediction_vectors"

    id = Column(Integer, primary_key=True)
    pixel_value = Column(Integer)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    prediction_raster_id = Column(
        Integer, ForeignKey("prediction_rasters.id"), nullable=False
    )
    prediction_raster = relationship("PredictionRaster", backref="prediction_vectors")

    def __init__(
        self, pixel_value: int, geometry: WKBElement, prediction_raster_id: int
    ):
        self.pixel_value = pixel_value
        self.geometry = geometry
        self.prediction_raster_id = prediction_raster_id


class PredictionRaster(Base):
    __tablename__ = "prediction_rasters"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    bbox = Column(Geometry(geometry_type="POLYGON", srid=4326))
    dtype = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    bands = Column(Integer)
    prediction_mask = Column(Raster, nullable=False)

    __table_args__ = (UniqueConstraint("timestamp", "bbox", name="uq_timestamp_bbox"),)

    def __init__(
        self,
        timestamp: datetime.datetime,
        bbox: WKBElement,
        dtype: str,
        width: int,
        height: int,
        bands: int,
        prediction_mask: RasterElement,
    ):
        self.timestamp = timestamp
        self.bbox = bbox
        self.dtype = dtype
        self.width = width
        self.height = height
        self.bands = bands
        self.prediction_mask = prediction_mask
