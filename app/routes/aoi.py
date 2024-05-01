import json

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func

from app.constants.geo import STANDARD_CRS, WORLD_WIDE_BBOX
from app.db.connect import Session
from app.db.models import AOI
from app.services.utils import parse_bbox

router = APIRouter()


@router.get("/aoi-centers")
def get_aoi_centers_by_bbox(
    bbox: str | None = Query(
        WORLD_WIDE_BBOX["query_str"],
        description="Comma-separated bounding box coordinates minx,miny,maxx,maxy  - WGS84",
    ),
):
    try:
        parsed_bbox = parse_bbox(bbox)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Bad Request. {e}")

    # Query for geometries within the bounding box
    session = Session()
    query = session.query(
        AOI.id,
        func.ST_AsGeoJSON(func.ST_Centroid(AOI.geometry)),
    ).filter(
        func.ST_Intersects(
            AOI.geometry,
            func.ST_MakeEnvelope(
                parsed_bbox.max_x,
                parsed_bbox.min_y,
                parsed_bbox.min_x,
                parsed_bbox.max_y,
                STANDARD_CRS["SRID"],
            ),
        ),
        AOI.is_deleted == False,  # noqa <E712>
    )
    results = query.all()
    session.close()

    results_list = [
        {
            "type": "Feature",
            "properties": {
                "id": row[0],
            },
            "geometry": json.loads(
                row[1]
            ),  # Ensuring row[3] is treated as a JSON string
        }
        for row in results
    ]

    results_dict = {"type": "FeatureCollection", "features": results_list}
    results_json = json.dumps(results_dict, ensure_ascii=False)
    return results_json


@router.get("/aoi")
def get_aoi_by_bbox(
    bbox: str | None = Query(
        WORLD_WIDE_BBOX["query_str"],
        description="Comma-separated bounding box coordinates minx,miny,maxx,maxy  - WGS84",
    ),
):
    try:
        parsed_bbox = parse_bbox(bbox)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Bad Request. {e}")

    # Query for geometries within the bounding box
    session = Session()
    query = session.query(
        AOI.id,
        AOI.name,
        AOI.created_at,
        func.ST_AsGeoJSON(AOI.geometry),
    ).filter(
        func.ST_Intersects(
            AOI.geometry,
            func.ST_MakeEnvelope(
                parsed_bbox.max_x,
                parsed_bbox.min_y,
                parsed_bbox.min_x,
                parsed_bbox.max_y,
                STANDARD_CRS["SRID"],
            ),
        ),
        AOI.is_deleted == False,  # noqa <E712>
    )
    results = query.all()
    session.close()

    results_list = [
        {
            "type": "Feature",
            "properties": {
                "id": row[0],
                "name": row[1],
                "created_at": row[2].isoformat(),
            },
            "geometry": json.loads(
                row[3]
            ),  # Ensuring row[3] is treated as a JSON string
        }
        for row in results
    ]

    results_dict = {"type": "FeatureCollection", "features": results_list}
    results_json = json.dumps(results_dict, ensure_ascii=False)
    return results_json
