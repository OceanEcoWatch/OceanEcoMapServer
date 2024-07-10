import datetime
import json

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func

from app.constants.spec import MAX_JOB_TIME_RANGE_DAYS
from app.db.connect import Session
from app.db.models import (
    AOI,
    Image,
    Job,
    JobStatus,
    Model,
    PredictionRaster,
    PredictionVector,
)
from app.utils import get_db

router = APIRouter()


@router.get("/jobs", tags=["Jobs"])
async def get_job_by_aoi(
    aoiId: int = Query(
        description="The id of the AOI",
    ),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Job.id.label("Job_id"),
            Job.status,
            Job.created_at,
            Job.aoi_id,
            Model.model_id,
            Image.id.label("Image_id"),
            Image.image_url,
            Image.timestamp,
            PredictionVector.pixel_value,
            func.ST_AsGeoJSON(PredictionVector.geometry).label(
                "PredictionVector_geometry"
            ),
        )
        .join(Model, Job.model_id == Model.id)
        .join(Image, Job.id == Image.job_id)
        .join(PredictionRaster, Image.id == PredictionRaster.image_id)
        .join(
            PredictionVector,
            PredictionRaster.id == PredictionVector.prediction_raster_id,
        )
        .filter(
            Job.aoi_id == aoiId,
            Job.is_deleted == False,  # noqa <E712>
            Job.status == JobStatus.COMPLETED,
        )
        .order_by(Job.id.desc(), Image.id.desc())
    )
    results = query.all()

    jobs = []

    last_job_id = -1
    last_image_id = -1
    new_job = {}

    # Loop through the sorted results and build the response.
    for row in results:
        # If the job_id is different from the last job_id, create a new job and append it to the jobs list.
        if row.Job_id != last_job_id:
            new_job = {
                "job_id": row.Job_id,
                "status": str(row.status),
                "created_at": row.created_at.timestamp(),
                "model_id": row.model_id,
                "images": [],
            }
            last_job_id = row.Job_id
            jobs.append(new_job)
        # If the image_id is different from the last image_id, create a new image and append it to the images list of the last job.
        if row.Image_id != last_image_id:
            jobs[-1]["images"].append(
                {
                    "image_id": row.Image_id,
                    "image_url": row.image_url,
                    "timestamp": row.timestamp.timestamp(),
                    "predictions": [],
                }
            )
        # Append the prediction to the predictions list of the last image. (the result only contains unique predictions)
        jobs[-1]["images"][-1]["predictions"].append(
            {
                "type": "Feature",
                "properties": {
                    "pixelValue": row.pixel_value,
                },
                "geometry": json.loads(row.PredictionVector_geometry),
            }
        )

        last_image_id = row.Image_id
        last_job_id = row.Job_id

    response = {"jobs": jobs}

    return json.dumps(response, ensure_ascii=False)


def enforce_time_range(start_date: datetime.datetime, end_date: datetime.datetime):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="The start date must be before the end date",
        )

    diff = end_date - start_date
    if diff.days > MAX_JOB_TIME_RANGE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"The time range must be less than {MAX_JOB_TIME_RANGE_DAYS} days",
        )


def split_date_range(
    start_date: datetime.datetime, end_date: datetime.datetime, max_days: int = 31
):
    delta = datetime.timedelta(days=max_days)
    current_start = start_date
    ranges = []
    while current_start < end_date:
        current_end = min(current_start + delta, end_date)
        ranges.append((current_start, current_end))
        current_start = current_end + datetime.timedelta(days=1)
    return ranges


@router.post("/jobs", tags=["Jobs"])
async def create_job(
    start_date: datetime.datetime = Body(
        description="The start date for the job",
    ),
    end_date: datetime.datetime = Body(
        description="The end date for the job",
    ),
    model_id: int = Body(
        description="The id of the model",
    ),
    aoi_id: int = Body(
        description="The id of the AOI",
    ),
    maxcc: float = Body(
        description="The maximum cloud coverage allowed in the requested images",
        le=1.0,
        ge=0.0,
    ),
    create_multiple: bool = Body(
        description="If true, multiple jobs will be created. For every 31 days in the time range a new job will be created.",
        default=False,
    ),
    db: Session = Depends(get_db),
):
    if create_multiple:
        date_ranges = split_date_range(start_date, end_date)
    else:
        enforce_time_range(start_date, end_date)
        date_ranges = [(start_date, end_date)]

    json_jobs = []
    if db.query(Model).filter(Model.id == model_id).count() == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    if db.query(AOI).filter(AOI.id == aoi_id).count() == 0:
        raise HTTPException(status_code=404, detail="AOI not found")
    for start, end in date_ranges:
        job = Job(
            status=JobStatus.PENDING,
            start_date=start,
            end_date=end,
            model_id=model_id,
            aoi_id=aoi_id,
            maxcc=maxcc,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        json_job = {
            "job_id": job.id,
            "status": str(job.status.value),
            "created_at": job.created_at.isoformat(),
            "start_date": job.start_date.isoformat(),
            "end_date": job.end_date.isoformat(),
            "maxcc": job.maxcc,
            "model_id": job.model_id,
            "images": [],
        }
        json_jobs.append(json_job)

    return json.dumps(json_jobs, ensure_ascii=False)


@router.get("/jobs/{job_id}", tags=["Jobs"])
async def get_job_by_id(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": str(job.status.value),
        "created_at": job.created_at.isoformat(),
        "start_date": job.start_date.isoformat(),
        "end_date": job.end_date.isoformat(),
        "maxcc": job.maxcc,
        "model_id": job.model_id,
    }
