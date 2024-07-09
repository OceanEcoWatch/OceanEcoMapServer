import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, func

from app.db.connect import Session
from app.db.models import AOI, Image, Job, SceneClassificationVector
from app.types.helpers import SCL

router = APIRouter()


@router.get("/scl", tags=["SCL"])
async def scl(
    classification: list[SCL] = Query(
        default=None, title="Classification values to filter by"
    ),
    aoi_id: int = Query(default=None, title="AOI ID to filter by"),
    timestamp: str = Query(default=None, title="Timestamp to filter by (ISO format)"),
):
    session = Session()

    try:
        if timestamp:
            timestamp_dt = datetime.fromisoformat(timestamp)
            start_of_day = datetime.combine(
                timestamp_dt.date(), datetime.min.time()
            ).replace(tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)
        else:
            start_of_day = None
            end_of_day = None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    aoi_in_db = session.query(AOI).filter_by(id=aoi_id).first()
    if not aoi_in_db:
        raise HTTPException(status_code=404, detail=f"No AOI found for ID: {aoi_id}")

    query = (
        session.query(
            func.ST_AsGeoJSON(SceneClassificationVector.geometry),
            SceneClassificationVector.pixel_value,
            SceneClassificationVector.image_id,
            Job.aoi_id.label("aoi_id"),
            Image.timestamp,
        )
        .select_from(SceneClassificationVector)
        .join(Image)
        .join(Job)
        .filter(Job.aoi_id == aoi_id)
    )

    if start_of_day and end_of_day:
        query = query.filter(
            and_(Image.timestamp >= start_of_day, Image.timestamp < end_of_day)
        )

    if classification:
        query = query.filter(SceneClassificationVector.pixel_value.in_(classification))

    results = query.all()

    if not results:
        raise HTTPException(status_code=404, detail="No SCL data found for query")
    print(results[0])
    results_list = [
        {
            "type": "Feature",
            "geometry": json.loads(result[0]),
            "properties": {
                "classification": SCL(
                    result.pixel_value
                ).name,  # Converting pixel value to enum name
                "image_id": result.image_id,
                "timestamp": result.timestamp.isoformat(),
                "aoi_id": result.aoi_id,
            },
        }
        for result in results
    ]

    results_dict = {"type": "FeatureCollection", "features": results_list}

    results_json = json.dumps(results_dict, ensure_ascii=False)
    session.close()
    return results_json
