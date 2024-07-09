import datetime
import enum

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    Boolean,
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


class ModelType(enum.Enum):
    SEGMENTATION = "SEGMENTATION"
    CLASSIFICATION = "CLASSIFICATION"


class Satellite(Base):
    __tablename__ = "satellites"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    bands = relationship(
        "Band", backref="satellite", cascade="all, delete, delete-orphan"
    )
    images = relationship(
        "Image", backref="satellite", cascade="all, delete, delete-orphan"
    )

    def __init__(self, name: str):
        self.name = name


class Band(Base):
    __tablename__ = "bands"

    id = Column(Integer, primary_key=True)
    satellite_id = Column(Integer, ForeignKey("satellites.id"), nullable=False)
    index = Column(Integer, nullable=False)  # 1-based index
    name = Column(String, nullable=False)
    description = Column(CONSTRAINT_STR, nullable=False)
    resolution = Column(Float, nullable=False)

    wavelength = Column(String, nullable=False)

    def __init__(
        self,
        satellite_id: int,
        index: int,
        name: str,
        description: str,
        resolution: float,
        wavelength: str,
    ):
        self.satellite_id = satellite_id
        self.index = index
        self.name = name
        self.description = description
        self.resolution = resolution
        self.wavelength = wavelength


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True)
    model_id = Column(CONSTRAINT_STR, nullable=False, unique=True)
    model_url = Column(CONSTRAINT_STR, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    version = Column(Integer, nullable=False, default=1)
    expected_image_height = Column(Integer, nullable=False)
    expected_image_width = Column(Integer, nullable=False)
    type = Column(Enum(ModelType), nullable=False)
    output_dtype = Column(Enum(*IMAGE_DTYPES, name="image_dtype"), nullable=False)
    expected_bands = relationship(
        "ModelBand", backref="model", cascade="all, delete, delete-orphan"
    )

    classification_classes = relationship(
        "ClassificationClass",
        backref="model",
        cascade="all, delete, delete-orphan",
    )
    jobs = relationship("Job", backref="model", cascade="all, delete, delete-orphan")

    def __init__(
        self,
        model_id: str,
        model_url: str,
        expected_image_height: int,
        expected_image_width: int,
        type: ModelType,
        output_dtype: str,
        created_at: datetime.datetime = datetime.datetime.now(),
        version: int = 1,
    ):
        self.model_id = model_id
        self.model_url = model_url
        self.expected_image_height = expected_image_height
        self.expected_image_width = expected_image_width
        self.type = type
        self.output_dtype = output_dtype
        self.created_at = created_at
        self.version = version


class ClassificationClass(Base):
    __tablename__ = "classification_classes"

    id = Column(Integer, primary_key=True)
    name = Column(CONSTRAINT_STR, nullable=False)
    index = Column(Integer, nullable=False)  # 1-based index

    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)

    def __init__(self, name: str, index: int, model_id: int):
        self.name = name
        self.index = index
        self.model_id = model_id


class ModelBand(Base):
    __tablename__ = "model_bands"

    model_id = Column(Integer, ForeignKey("models.id"), primary_key=True)
    band_id = Column(Integer, ForeignKey("bands.id"), primary_key=True)

    def __init__(self, model_id: int, band_id: int):
        self.model_id = model_id
        self.band_id = band_id


class AOI(Base):
    __tablename__ = "aois"

    id = Column(Integer, primary_key=True)
    name = Column(CONSTRAINT_STR, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    is_deleted = Column(Boolean, nullable=False, default=False)
    geometry = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    jobs = relationship("Job", backref="aoi", cascade="all, delete, delete-orphan")

    def __init__(
        self,
        name: str,
        geometry,
        created_at: datetime.datetime = datetime.datetime.now(),
    ):
        self.name = name
        self.geometry = geometry
        self.created_at = created_at


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    status = Column(
        Enum(JobStatus, name="job_status"),
        nullable=False,
        default=JobStatus.PENDING,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)
    is_deleted = Column(Boolean, nullable=False, default=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    maxcc = Column(Float, nullable=False)
    aoi_id = Column(Integer, ForeignKey("aois.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)

    images = relationship("Image", backref="job", cascade="all, delete, delete-orphan")

    def __init__(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        maxcc: float,
        aoi_id: int,
        model_id: int,
        status: JobStatus = JobStatus.PENDING,
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.maxcc = maxcc
        self.aoi_id = aoi_id
        self.model_id = model_id
        self.status = status


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (UniqueConstraint("image_id", "timestamp", "bbox", "job_id"),)

    id = Column(Integer, primary_key=True)
    satellite_id = Column(Integer, ForeignKey("satellites.id"), nullable=False)
    image_id = Column(CONSTRAINT_STR, nullable=False)
    image_url = Column(CONSTRAINT_STR, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    dtype = Column(
        Enum(*IMAGE_DTYPES, name="image_dtype"),
        nullable=False,
    )
    crs = Column(Integer, nullable=False)
    resolution = Column(Float, nullable=False)
    image_width = Column(Integer, nullable=False)
    image_height = Column(Integer, nullable=False)
    bbox = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    prediction_raster = relationship(
        "PredictionRaster", backref="image", cascade="all, delete, delete-orphan"
    )
    scene_classification_vectors = relationship(
        "SceneClassificationVector",
        backref="image",
        cascade="all, delete, delete-orphan",
    )

    def __init__(
        self,
        satellite_id: int,
        image_id: str,
        image_url: str,
        timestamp: datetime.datetime,
        dtype: str,
        crs: int,
        resolution: float,
        image_width: int,
        image_height: int,
        bbox,
        job_id: int,
    ):
        self.satellite_id = satellite_id
        self.image_id = image_id
        self.image_url = image_url
        self.timestamp = timestamp
        self.dtype = dtype
        self.crs = crs
        self.resolution = resolution
        self.image_width = image_width
        self.image_height = image_height
        self.bbox = bbox
        self.job_id = job_id


class PredictionRaster(Base):
    __tablename__ = "prediction_rasters"

    id = Column(Integer, primary_key=True)
    raster_url = Column(CONSTRAINT_STR, nullable=False)
    dtype = Column(
        Enum(*IMAGE_DTYPES, name="image_dtype"),
        nullable=False,
    )
    image_width = Column(Integer, nullable=False)
    image_height = Column(Integer, nullable=False)
    bbox = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    image_id = Column(Integer, ForeignKey("images.id"), nullable=False, unique=True)
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
        bbox,
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
        Integer, ForeignKey("prediction_rasters.id"), nullable=False, index=True
    )

    def __init__(
        self, pixel_value: int, geometry: WKBElement, prediction_raster_id: int
    ):
        self.pixel_value = pixel_value
        self.geometry = geometry
        self.prediction_raster_id = prediction_raster_id


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
