import json

from fastapi import APIRouter
from sqlalchemy import func

from app.config.config import DEFAULT_MAX_ROW_LIMIT
from app.db.connect import Session
from app.db.models import PredictionVector

router = APIRouter()


@router.get("/predictions")
def get_predictions(limit: int):
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
