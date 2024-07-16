import datetime
import json

from db.connect import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.db.connect import Session
from app.db.models import (
    Band,
    ClassificationClass,
    Model,
    ModelBand,
    ModelType,
    Satellite,
)

router = APIRouter()


class ModelCreate(BaseModel):
    model_id: str = Field(..., example="oceanecowatch/plasticdetectionmodel:1.0.1")
    model_url: str = Field(...)
    expected_image_height: int = Field(..., example=480)
    expected_image_width: int = Field(..., example=480)
    type: ModelType = Field(..., example=ModelType.SEGMENTATION)
    output_dtype: str = Field(..., example="uint8")
    version: int = Field(..., example=1)
    satellite_name: str = Field(..., example="SENTINEL2_L2A")
    band_indices: list[int] = Field(
        ..., example=[1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]
    )
    classification_classes: dict[str, int] = Field(..., example={"Marine debris": 0})


@router.get("/model", tags=["Model"])
async def get_model(
    model_id: str | None = Query(None, description="Model ID"),
    model_url: str | None = Query(None, description="Model URL"),
    version: int | None = Query(None, description="Model Version"),
    model_type: ModelType | None = Query(None, description="Model Type"),
    db: Session = Depends(get_db),
):
    models = db.query(Model)
    if model_id:
        models = models.filter(Model.model_id == model_id)
    if model_url:
        models = models.filter(Model.model_url == model_url)
    if version:
        models = models.filter(Model.version == version)
    if model_type:
        models = models.filter(Model.type == model_type)

    json_models = [
        {
            "model_id": model.model_id,
            "model_url": model.model_url,
            "expected_image_height": model.expected_image_height,
            "expected_image_width": model.expected_image_width,
            "output_dtype": model.output_dtype,
            "type": model.type,
            "version": model.version,
        }
        for model in models
    ]

    return json_models


@router.post("/model", tags=["Model"])
def create_model(model: ModelCreate, db: Session = Depends(get_db)):
    # Check if the satellite exists by name
    satellite = (
        db.query(Satellite).filter(Satellite.name == model.satellite_name).first()
    )
    if not satellite:
        return HTTPException(
            status_code=404, detail="Satellite not found with the given name"
        )

    # Create the model instance
    db_model = Model(
        model_id=model.model_id,
        model_url=model.model_url,
        expected_image_height=model.expected_image_height,
        expected_image_width=model.expected_image_width,
        type=model.type,
        output_dtype=model.output_dtype,
        created_at=datetime.datetime.now(),
        version=model.version,
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)

    # Fetch the bands based on the index and satellite ID
    bands = (
        db.query(Band)
        .filter(Band.satellite_id == satellite.id, Band.index.in_(model.band_indices))
        .all()
    )

    # Create ModelBand instances
    model_bands = [ModelBand(model_id=db_model.id, band_id=band.id) for band in bands]
    db.add_all(model_bands)
    db.commit()
    db.refresh(db_model)

    # create classification classes
    classification_classes = [
        ClassificationClass(
            model_id=db_model.id,
            name=classification_class,
            index=index,
        )
        for classification_class, index in model.classification_classes.items()
    ]
    db.add_all(classification_classes)
    db.commit()
    db.refresh(db_model)

    return json.dumps(
        {
            "model_id": db_model.model_id,
            "model_url": db_model.model_url,
            "expected_image_height": db_model.expected_image_height,
            "expected_image_width": db_model.expected_image_width,
            "output_dtype": db_model.output_dtype,
            "type": db_model.type.value,
            "version": db_model.version,
            "bands": [
                {
                    "index": band.index,
                    "name": band.name,
                    "description": band.description,
                    "resolution": band.resolution,
                    "wavelength": band.wavelength,
                }
                for band in bands
            ],
            "classification_classes": [
                {
                    "name": classification_class.name,
                    "index": classification_class.index,
                }
                for classification_class in classification_classes
            ],
        }
    )
