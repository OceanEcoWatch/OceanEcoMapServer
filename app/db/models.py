from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PredictionVector(Base):
    __tablename__ = "prediction_vectors"

    id = Column(Integer, primary_key=True)
    pixel_value = Column(Integer, nullable=False)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    sentinel_hub_response_id = Column(Integer)

    def __init__(
        self, pixel_value: int, geometry: WKBElement, sentinel_hub_response_id: int
    ):
        self.pixel_value = pixel_value
        self.geometry = geometry
        self.sentinel_hub_response_id = sentinel_hub_response_id
