import json
from datetime import datetime, timedelta, timezone

import requests
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func

from app.config.config import DEFAULT_MAX_ROW_LIMIT, GITHUB_TOKEN
from app.db.connect import Session
from app.db.models import (
    AOI,
    ClassificationClass,
    Image,
    Job,
    JobStatus,
    Model,
    ModelType,
    PredictionRaster,
    PredictionVector,
)
from app.utils import accuracy_limit_to_percent, percent_to_accuracy

router = APIRouter()


@router.get("/images-by-day", tags=["AOI"])
async def get_aoi_images_grouped_by_day(
    aoiId: int = Query(..., description="Id of the AOI in question"),
):
    session = Session()
    query = (
        session.query(
            Image.id,
            Image.timestamp,
            func.ST_AsGeoJSON(Image.bbox).label("geometry"),
        )
        .join(
            Job,
            Image.job_id == Job.id,
        )
        .filter(
            Job.aoi_id == aoiId,
        )
        .order_by(Image.timestamp)
    )

    results = query.all()
    session.close()

    days = {}
    for row in results:
        start_of_day = await get_start_of_day_unix_timestamp(row.timestamp)
        row_data = {
            "image_id": row.id,
            "timestamp": row.timestamp.timestamp(),
            "geometry": json.loads(row.geometry),
        }
        if start_of_day not in days:
            days[start_of_day] = [row_data]
        else:
            days[start_of_day].append(row_data)
    return JSONResponse(content=days)


async def get_start_of_day_unix_timestamp(date_time):
    utc = date_time.astimezone(timezone.utc)
    start_of_utc_day = datetime(utc.year, utc.month, utc.day, tzinfo=timezone.utc)
    return start_of_utc_day.timestamp()


@router.get("/predictions-by-day-and-aoi", tags=["Predictions"])
async def get_predictions_by_day(
    day: int = Query(
        ...,
        description="Unix Timestamp of the day in question. The timestamp will set the beginning of a 24hr time range. The endpoint will return all predictions for the area of the aoi in this timeframe.",
    ),
    aoi_id: int = Query(
        ...,
    ),
    model_id: str = Query(
        default=None, description="Optional, filter predictions based on model"
    ),
    accuracy_limit: int = Query(
        default=None,
        description="The minimum accuracy of the prediction to be included in the results lowest value: 0 (returning all data) | highest value: 100 (returning minimal data). For example: 50. Only for SEGMENTATION models",
    ),
):
    session = Session()
    try:
        aoi = session.query(AOI).filter(AOI.id == aoi_id).one_or_none()
        if not aoi:
            raise HTTPException(status_code=404, detail="AOI not found")

        startDate = datetime.fromtimestamp(day)
        endDate = startDate + timedelta(days=1)

        query = (
            session.query(
                AOI.id,
                Image.timestamp,
                Image.id,
                Model.model_id,
                Model.type.label("model_type"),
                func.array_agg(ClassificationClass.name).label(
                    "classification_classes"
                ),
                func.ST_AsGeoJSON(PredictionVector.geometry).label("geometry"),
                PredictionVector.pixel_value,
            )
            .join(Job, Job.aoi_id == AOI.id)
            .join(Image, Image.job_id == Job.id)
            .join(PredictionRaster, PredictionRaster.image_id == Image.id)
            .join(
                PredictionVector,
                PredictionVector.prediction_raster_id == PredictionRaster.id,
            )
            .join(Model, Model.id == Job.model_id)
            .outerjoin(ClassificationClass, ClassificationClass.model_id == Model.id)
            .filter(
                Image.timestamp >= startDate,
                Image.timestamp < endDate,
                func.ST_Intersects(
                    PredictionVector.geometry,
                    AOI.geometry,
                ),
                AOI.id == aoi_id,
            )
            .group_by(
                AOI.id,
                Image.timestamp,
                Image.id,
                Model.model_id,
                Model.type,
                PredictionVector.geometry,
                PredictionVector.pixel_value,
            )
        )
        if model_id:
            model = (
                session.query(Model).filter(Model.model_id == model_id).one_or_none()
            )
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            query = query.filter(Model.model_id == model_id)

        if accuracy_limit:
            max_pixel_value = round(percent_to_accuracy(accuracy_limit))
            query = query.filter(PredictionVector.pixel_value >= max_pixel_value)

        query = query.order_by(Image.timestamp).limit(DEFAULT_MAX_ROW_LIMIT)
        results = query.all()
        results_list = [
            {
                "type": "Feature",
                "properties": {
                    "pixelValue": accuracy_limit_to_percent(row.pixel_value)
                    if row.model_type == ModelType.SEGMENTATION
                    else row.pixel_value,
                    "timestamp": row.timestamp.timestamp(),
                    "modelId": row.model_id,
                    "modelType": row.model_type.value,
                    "classificationClasses": row.classification_classes,
                },
                "geometry": json.loads(row.geometry),
            }
            for row in results
        ]

        results_dict = {"type": "FeatureCollection", "features": results_list}
        return JSONResponse(content=results_dict)
    finally:
        session.close()


@router.get("/predictions", tags=["Predictions"])
async def get_predictions(limit: int = DEFAULT_MAX_ROW_LIMIT):
    limit = min(
        limit, DEFAULT_MAX_ROW_LIMIT
    )  # DEFAULT_MAX_ROW_LIMIT will always be the max limit
    session = Session()
    query = session.query(
        func.ST_AsGeoJSON(PredictionVector.geometry),
        PredictionVector.pixel_value,
    ).limit(limit)
    results = query.all()

    results_list = [
        {
            "type": "Feature",
            "properties": {"pixelValue": row[1]},
            # Ensuring row[0] is treated as a JSON string
            "geometry": json.loads(row[0]),
        }
        for row in results
    ]

    results_dict = {"type": "FeatureCollection", "features": results_list}

    results_json = json.dumps(results_dict, ensure_ascii=False)
    session.close()
    return results_json


@router.post("/predictions", tags=["Predictions"])
async def run_prediction_jobs(
    job_ids: list[int] = Query(
        ...,
        description="List of job IDs to run the predictions for",
    ),
    probability_threshold: float = Query(
        0.33,
        description="The minimum probability of the prediction to be included in the results",
    ),
):
    session = Session()
    try:
        results = []
        for job_id in job_ids:
            job = session.query(Job).filter(Job.id == job_id).one_or_none()
            if not job:
                raise HTTPException(
                    status_code=404, detail=f"Job with ID {job_id} not found"
                )
            if job.status == JobStatus.COMPLETED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Job with ID {job_id} already completed",
                )
            token = GITHUB_TOKEN
            if not token:
                raise HTTPException(
                    status_code=500,
                    detail="GITHUB_TOKEN not set",
                )
            owner = "OceanEcoWatch"
            repo = "PlasticDetectionService"
            workflow_id = "job.yml"  # You can find this in the workflow URL

            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {token}",
            }

            data = {
                "ref": "main",  # The branch or tag to run the workflow on
                "inputs": {
                    "job_id": str(job.id),
                    "probability_threshold": str(probability_threshold),
                },
            }

            response = requests.post(
                f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
                headers=headers,
                json=data,
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error running prediction job for job ID {job_id}: {err}",
                )
            results.append({"job_id": job_id, "message": "Prediction job started"})

    finally:
        session.close()

    return {"results": results}
