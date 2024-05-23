import json

from fastapi import APIRouter, Body, Query

from app.db.connect import Session
from app.db.models import Model

router = APIRouter()


@router.get("/model", tags=["Model"])
async def get_model(
    model_id: str | None = Query(None, description="Model ID"),
    model_url: str | None = Query(None, description="Model URL"),
    version: int | None = Query(None, description="Model version"),
):
    session = Session()
    try:
        models = (
            session.query(Model)
            .filter(
                Model.model_id == model_id,
                Model.model_url == model_url,
                Model.version == version,
            )
            .all()
        )
        json_models = [
            {
                "model_id": model.model_id,
                "model_url": model.model_url,
                "version": model.version,
            }
            for model in models
        ]
    finally:
        session.close()

    return json_models


@router.post("/model", tags=["Model"])
async def post_model(
    model_id: str = Body(..., description="Model ID"),
    model_url: str = Body(..., description="Model URL"),
    version: int = Body(..., description="Model version"),
):
    session = Session()
    try:
        model = Model(
            model_id=model_id,
            model_url=model_url,
            version=version,
        )
        session.add(model)
        session.commit()
        json_model = json.dumps(
            {
                "model_id": model.model_id,
                "model_url": model.model_url,
                "version": model.version,
            }
        )
    finally:
        session.close()

    return json_model
