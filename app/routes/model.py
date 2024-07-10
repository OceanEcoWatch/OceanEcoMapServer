import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.db.connect import Session
from app.db.models import Model, ModelType
from app.utils import get_db

router = APIRouter()


class ModelCreate(BaseModel):
    model_id: str = Field(...)
    model_url: str = Field(...)
    expected_image_height: int = Field(..., example=480)
    expected_image_width: int = Field(..., example=480)
    type: ModelType = Field(..., example=ModelType.SEGMENTATION)
    output_dtype: str = Field(..., example="uint8")
    version: int = Field(..., example=1)


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
    return db_model
