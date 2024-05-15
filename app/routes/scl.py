import json

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func

from app.db.connect import Session
from app.db.models import SceneClassificationVector
from fas
router = APIRouter()


class SCL(enum.Enum):
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
    def check(cls, value):
        return value in cls.__members__.values()


@router.get("/scl")
def get_scl(
    classification: list[int] = Query(
        default=None, title="Classification values to filter by"
    ),
):
    if classification:
        for value in classification:
            if not SCL.check(value):
                raise HTTPException(
                    status_code=400, detail=f"Invalid classification value: {value}"
                )

    session = Session()
    query = session.query(
        func.ST_AsGeoJSON(SceneClassificationVector.geometry),
        SceneClassificationVector.pixel_value,
    ).filter(SceneClassificationVector.pixel_value == classification)
    results = query.all()

    results_list = [
        {
            "type": "Feature",
            "geometry": json.loads(result[0]),
            "properties": {"pixel_value": result[1]},
        }
        for result in results
    ]

    results_dict = {"type": "FeatureCollection", "features": results_list}

    results_json = json.dumps(results_dict, ensure_ascii=False)
    session.close()
    return results_json
