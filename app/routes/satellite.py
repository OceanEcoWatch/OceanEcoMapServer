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
