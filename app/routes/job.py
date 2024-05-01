import json

from fastapi import APIRouter, Query
from sqlalchemy import func

from app.db.connect import Session
from app.db.models import (
    Image,
    Job,
    JobStatus,
    Model,
    PredictionRaster,
    PredictionVector,
)

router = APIRouter()


@router.get("/jobs")
def get_job_by_aoi(
    aoiId: int = Query(
        description="The id of the AOI",
    ),
):
    session = Session()
    query = (
        session.query(
            Job.id.label("Job_id"),
            Job.status,
            Job.created_at,
            Job.aoi_id,
            Model.model_id,
            Image.id.label("Image_id"),
            Image.image_url,
            Image.timestamp,
            Image.provider,
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
    session.close()

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
                    "provider": row.provider,
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
    print(len(response["jobs"]))
    print(len(response["jobs"][0]["images"]))
    print(len(response["jobs"][0]["images"][0]["predictions"]))
    return json.dumps(response, ensure_ascii=False)
