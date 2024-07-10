import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.connect import Session
from app.db.models import (
    Band,
    Satellite,
)
from app.utils import get_db

router = APIRouter()


class BandCreate(BaseModel):
    index: int
    name: str
    description: str
    resolution: float
    wavelength: str


class SatelliteCreate(BaseModel):
    name: str = Field(..., example="SENTINEL2_L1C")
    bands: list[BandCreate] = Field(
        ...,
        example=[
            {
                "index": 1,
                "name": "B01",
                "description": "Coastal aerosol",
                "resolution": 60.0,
                "wavelength": "443nm",
            },
            {
                "index": 2,
                "name": "B02",
                "description": "Blue",
                "resolution": 10.0,
                "wavelength": "492nm",
            },
            {
                "index": 3,
                "name": "B03",
                "description": "Green",
                "resolution": 10.0,
                "wavelength": "560nm",
            },
            {
                "index": 4,
                "name": "B04",
                "description": "Red",
                "resolution": 10.0,
                "wavelength": "665nm",
            },
            {
                "index": 5,
                "name": "B05",
                "description": "Red edge 1",
                "resolution": 20.0,
                "wavelength": "705nm",
            },
            {
                "index": 6,
                "name": "B06",
                "description": "Red edge 2",
                "resolution": 20.0,
                "wavelength": "740nm",
            },
            {
                "index": 7,
                "name": "B07",
                "description": "Red edge 3",
                "resolution": 20.0,
                "wavelength": "783nm",
            },
            {
                "index": 8,
                "name": "B08",
                "description": "NIR",
                "resolution": 10.0,
                "wavelength": "832nm",
            },
            {
                "index": 9,
                "name": "B8A",
                "description": "Narrow NIR",
                "resolution": 20.0,
                "wavelength": "865nm",
            },
            {
                "index": 10,
                "name": "B09",
                "description": "Water vapor",
                "resolution": 60.0,
                "wavelength": "945nm",
            },
            {
                "index": 11,
                "name": "B10",
                "description": "SWIR - Cirrus",
                "resolution": 60.0,
                "wavelength": "1375nm",
            },
            {
                "index": 12,
                "name": "B11",
                "description": "SWIR 1",
                "resolution": 20.0,
                "wavelength": "1610nm",
            },
            {
                "index": 13,
                "name": "B12",
                "description": "SWIR 2",
                "resolution": 20.0,
                "wavelength": "2190nm",
            },
        ],
    )


@router.post("/satellites/", tags=["Satellites"])
def create_satellite(satellite: SatelliteCreate, db: Session = Depends(get_db)):
    db_satellite = Satellite(name=satellite.name)
    db.add(db_satellite)
    db.commit()
    db.refresh(db_satellite)

    for band in satellite.bands:
        db_band = Band(
            satellite_id=db_satellite.id,
            index=band.index,
            name=band.name,
            description=band.description,
            resolution=band.resolution,
            wavelength=band.wavelength,
        )
        db.add(db_band)

    db.commit()
    return json.dumps(
        {
            "id": db_satellite.id,
            "name": db_satellite.name,
            "bands": [
                {
                    "index": band.index,
                    "name": band.name,
                    "description": band.description,
                    "resolution": band.resolution,
                    "wavelength": band.wavelength,
                }
                for band in db_satellite.bands
            ],
        },
        ensure_ascii=False,
    )
