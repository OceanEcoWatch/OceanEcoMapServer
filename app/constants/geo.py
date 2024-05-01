from app.types.helpers import BoundingBox

STANDARD_CRS = {
    "EPSG": "EPSG:4326",
    "string": "WGS84",
    "SRID": 4326,
}

WORLD_WIDE_BBOX = {
    "bbox": BoundingBox(
        -180,
        -90,
        180,
        190,
    ),
    "query_str": "-180,-90,180,90",
}
