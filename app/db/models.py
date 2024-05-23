import datetime
import enum

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship  # type: ignore

from app.types.helpers import IMAGE_DTYPES

Base = declarative_base()

CONSTRAINT_STR = String(255)


class JobStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AOI(Base):
    __tablename__ = "aois"

    id = Column(Integer, primary_key=True)
    name = Column(CONSTRAINT_STR, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    is_deleted = Column(Boolean, nullable=False, default=False)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    def __init__(
        self,
        name: str,
        geometry: WKBElement,
        is_deleted: bool = False,
        created_at: datetime.datetime = datetime.datetime.now(),
    ):
        self.name = name
        self.created_at = created_at
        self.geometry = geometry
        self.is_deleted = is_deleted


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    model_id = Column(CONSTRAINT_STR, nullable=False, unique=True)
    model_url = Column(CONSTRAINT_STR, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    version = Column(Integer, nullable=False, default=1)

    def __init__(
        self,
        model_id: str,
        model_url: str,
        version: int = 1,
        created_at: datetime.datetime = datetime.datetime.now(),
    ):
        self.model_id = model_id
        self.model_url = model_url
        self.version = version
        self.created_at = created_at


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    status = Column(
        Enum(JobStatus, name="job_status"),
        nullable=False,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    is_deleted = Column(Boolean, nullable=False, default=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    maxcc = Column(Float, nullable=False)
    aoi_id = Column(Integer, ForeignKey("aois.id"), nullable=False)
    aoi = relationship("AOI", backref="jobs")
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    model = relationship("Model", backref="jobs")

    def __init__(
        self,
        status: JobStatus,
        aoi_id: int,
        model_id: int,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        maxcc: float,
        is_deleted: bool = False,
        created_at: datetime.datetime = datetime.datetime.now(),
    ):
        self.status = status
        self.created_at = created_at
        self.aoi_id = aoi_id
        self.model_id = model_id
        self.start_date = start_date
        self.end_date = end_date
        self.maxcc = maxcc
        self.is_deleted = is_deleted


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (UniqueConstraint("image_id", "timestamp", "bbox"),)

    id = Column(Integer, primary_key=True)
    image_id = Column(CONSTRAINT_STR, nullable=False)
    image_url = Column(CONSTRAINT_STR, nullable=False, unique=True)
    timestamp = Column(DateTime, nullable=False)
    dtype = Column(
        Enum(*IMAGE_DTYPES, name="image_dtype"),
        nullable=False,
    )
    crs = Column(Integer, nullable=False)
    resolution = Column(Float, nullable=False)
    image_width = Column(Integer, nullable=False)
    image_height = Column(Integer, nullable=False)
    bands = Column(Integer, CheckConstraint("bands>0 AND bands<=100"), nullable=False)
    provider = Column(CONSTRAINT_STR, nullable=False)
    bbox = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    jobs = relationship("Job", backref="images")

    prediction_rasters = relationship(
        "PredictionRaster", backref="image", cascade="all, delete, delete-orphan"
    )
    scene_classification_vectors = relationship(
        "SceneClassificationVector",
        backref="image",
        cascade="all, delete, delete-orphan",
    )

    def __init__(
        self,
        image_id: str,
        image_url: str,
        timestamp: datetime.datetime,
        dtype: str,
        crs: int,
        resolution: float,
        image_width: int,
        image_height: int,
        bands: int,
        provider: str,
        bbox: WKBElement,
        job_id: int,
    ):
        self.image_id = image_id
        self.image_url = image_url
        self.timestamp = timestamp
        self.dtype = dtype
        self.crs = crs
        self.resolution = resolution
        self.image_width = image_width
        self.image_height = image_height
        self.bands = bands
        self.provider = provider
        self.bbox = bbox
        self.job_id = job_id


class PredictionRaster(Base):
    __tablename__ = "prediction_rasters"

    id = Column(Integer, primary_key=True)
    raster_url = Column(CONSTRAINT_STR, nullable=False, unique=True)
    dtype = Column(
        Enum(*IMAGE_DTYPES, name="image_dtype"),
        nullable=False,
    )
    image_width = Column(Integer, nullable=False)
    image_height = Column(Integer, nullable=False)
    bbox = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    prediction_vectors = relationship(
        "PredictionVector",
        backref="prediction_raster",
        cascade="all, delete, delete-orphan",
    )

    def __init__(
        self,
        raster_url: str,
        dtype: str,
        image_width: int,
        image_height: int,
        bbox: WKBElement,
        image_id: int,
    ):
        self.raster_url = raster_url
        self.dtype = dtype
        self.image_width = image_width
        self.image_height = image_height
        self.bbox = bbox
        self.image_id = image_id


class PredictionVector(Base):
    __tablename__ = "prediction_vectors"

    id = Column(Integer, primary_key=True)
    pixel_value = Column(Integer, nullable=False)
    geometry = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    prediction_raster_id = Column(
        Integer, ForeignKey("prediction_rasters.id"), nullable=False
    )

    def __init__(self, pixel_value: int, geometry: WKBElement, raster_id: int):
        self.pixel_value = pixel_value
        self.geometry = geometry

        self.prediction_raster_id = raster_id


class SceneClassificationVector(Base):
    __tablename__ = "scene_classification_vectors"

    id = Column(Integer, primary_key=True)
    pixel_value = Column(Integer, nullable=False)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)

    def __init__(self, pixel_value: int, geometry: WKBElement, image_id: int):
        self.pixel_value = pixel_value
        self.geometry = geometry
        self.image_id = image_id
