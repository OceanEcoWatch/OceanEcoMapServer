import enum
import json

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func

from app.db.connect import Session
from app.db.models import Image, SceneClassificationVector

router = APIRouter()


class SCL(enum.IntEnum):
    NO_DATA = 0
    SATURATED = 1
    SHADOWS = 2
    CLOUD_SHADOWS = 3
    VEGETATION = 4
    NOT_VEGETATED = 5
    WATER = 6
    UNCLASSIFIED = 7
    CLOUD_MEDIUM_PROB = 8
    CLOUD_HIGH_PROB = 9
    THIN_CIRRUS = 10
    SNOW_ICE = 11

    @classmethod
    def is_valid(cls, value):
        return value in cls.__members__.values()


@router.get("/scl")
def scl(
    classification: list[int] = Query(
        default=None, title="Classification values to filter by"
    ),
    image_id: int = Query(default=None, title="Image ID to filter by"),
    geometry: str = Query(
        default=None,
        title="GeoJSON geometry to filter by",
    ),
):
    session = Session()

    if classification:
        for value in classification:
            if not SCL.is_valid(value):
                raise HTTPException(
                    status_code=400, detail=f"Invalid classification value: {value}"
                )
    if image_id:
        image_in_db = session.query(Image).filter_by(id=image_id).first()
        if not image_in_db:
            raise HTTPException(
                status_code=404, detail=f"No image found for ID: {image_id}"
            )
        image_rel = (
            session.query(SceneClassificationVector)
            .filter_by(image_id=image_id)
            .first()
        )
        if not image_rel:
            raise HTTPException(
                status_code=404, detail=f"No SCL data found for image ID: {image_id}"
            )

    query = session.query(
        func.ST_AsGeoJSON(SceneClassificationVector.geometry),
        SceneClassificationVector.pixel_value,
        SceneClassificationVector.image_id,
    )

    if classification:
        query = query.filter(SceneClassificationVector.pixel_value.in_(classification))
    if image_id:
        query = query.filter(SceneClassificationVector.image_id == image_id)

    if geometry:
        query = query.filter(
            func.ST_Intersects(
                SceneClassificationVector.geometry,
                func.ST_GeomFromGeoJSON(geometry),
            )
        )

    results = query.all()

    if not results:
        raise HTTPException(status_code=404, detail="No SCL data found for query")

    results_list = [
        {
            "type": "Feature",
            "geometry": json.loads(result[0]),
            "properties": {
                "classification": result[1],
                "image_id": result[2],
            },
        }
        for result in results
    ]

    results_dict = {"type": "FeatureCollection", "features": results_list}

    results_json = json.dumps(results_dict, ensure_ascii=False)
    session.close()
    return results_json
