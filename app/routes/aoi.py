import json

import geopandas as gpd
from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from shapely.geometry import shape
from sqlalchemy import func

from app.constants.geo import STANDARD_CRS, WORLD_WIDE_BBOX
from app.constants.spec import MAX_AOI_SQKM
from app.db.connect import Session
from app.db.models import AOI
from app.services.utils import determine_utm_epsg, parse_bbox
from app.types.helpers import PolygonFeature, PolygonFeatureCollection, PolygonGeoJSON

router = APIRouter()


@router.get("/aoi-centers", tags=["AOI"])
async def get_aoi_centers_by_bbox(
    bbox: str | None = Query(
        WORLD_WIDE_BBOX["query_str"],
        description="Comma-separated bounding box coordinates minx,miny,maxx,maxy  - WGS84",
    ),
):
    try:
        parsed_bbox = parse_bbox(bbox)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Bad Request. {e}")

    session = Session()

    # Query for geometries within the bounding box
    query = session.query(
        AOI.id,
        AOI.name,
        func.ST_AsGeoJSON(func.ST_Centroid(AOI.geometry)).label("geometry"),
        func.ST_AsText(AOI.geometry).label("aoi_as_wkt"),
        func.ST_AsGeoJSON(AOI.geometry).label("aoi_geo")
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

    results_list = []
    for row in results:
        # Convert WKT to GeoSeries and create GeoDataFrame
        polygon = gpd.GeoSeries.from_wkt([row.aoi_as_wkt]).iloc[0]
        gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polygon])

        # Get bounding box
        bbox = gdf.total_bounds
        west_lon, south_lat, east_lon, north_lat = bbox[0], bbox[1], bbox[2], bbox[3]

        # Determine local EPSG
        local_epsg = determine_utm_epsg(
            source_epsg=4326,
            west_lon=west_lon,
            south_lat=south_lat,
            east_lon=east_lon,
            north_lat=north_lat,
            contains=True,
        )
        # Convert to local CRS
        localized_gdf = gdf.to_crs(epsg=local_epsg)
        localized_polygon = localized_gdf.iloc[0].geometry

        # Calculate area in km^2
        area_km2 = localized_polygon.area / 1e6  # Convert to km^2

        # Create bounding box as array
        bounding_box = [west_lon, south_lat, east_lon, north_lat]

        results_list.append(
            {
                "type": "Feature",
                "properties": {
                    "name": row.name,
                    "id": row.id,
                    "area_km2": area_km2,
                    "polygon": json.loads(row.aoi_geo),
                    "bbox": bounding_box
                },
                # Ensuring row.geometry is treated as a JSON string
                "geometry": json.loads(row.geometry),
            }
        )

    results_dict = {"type": "FeatureCollection", "features": results_list}
    results_json = json.dumps(results_dict, ensure_ascii=False)
    return JSONResponse(content=results_json)


@router.get("/aoi", tags=["AOI"])
async def get_aoi_by_bbox(
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
            # Ensuring row[3] is treated as a JSON string
            "geometry": json.loads(row[3]),
        }
        for row in results
    ]

    results_dict = {"type": "FeatureCollection", "features": results_list}
    results_json = json.dumps(results_dict, ensure_ascii=False)
    return results_json


def enforce_max_aoi_area(area_km2: float):
    if area_km2 > MAX_AOI_SQKM:
        raise HTTPException(
            status_code=400, detail="Area of Interest exceeds maximum area of 100 km^2"
        )


@router.post("/aoi", tags=["AOI"])
async def create_aoi(
    name: str = Body(
        description="Name of the AOI",
    ),
    geometry: PolygonGeoJSON = Body(
        description="Polygon GeoJSON object representing the AOI. If a FeatureCollection is provided, only the first feature will be used.",
    ),
):
    if isinstance(geometry, PolygonFeatureCollection):
        geometry = geometry.features[0].geometry
    elif isinstance(geometry, PolygonFeature):
        geometry = geometry.geometry

    polygon = shape(geometry.model_dump())

    gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[polygon])
    local_utm_epsg = determine_utm_epsg(
        source_epsg=4326,
        west_lon=gdf.total_bounds[0],
        south_lat=gdf.total_bounds[1],
        east_lon=gdf.total_bounds[2],
        north_lat=gdf.total_bounds[3],
        contains=True,
    )
    localized_gdf = gdf.to_crs(epsg=local_utm_epsg)
    localized_polygon = localized_gdf.iloc[0].geometry

    area_km2 = localized_polygon.area / 1e6

    enforce_max_aoi_area(area_km2)
    session = Session()
    try:
        aoi = AOI(
            name=name,
            geometry=func.ST_GeomFromGeoJSON(
                json.dumps(geometry.model_dump())),
        )
        session.add(aoi)
        session.commit()

        json_aoi = json.dumps(
            {
                "id": aoi.id,
                "name": aoi.name,
                "created_at": aoi.created_at.isoformat(),
            }
        )
    finally:
        session.close()

    return json_aoi
