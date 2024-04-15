from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, validator

from app.services.sh_catalog import query_sh_catalog


class CustomPolygon(BaseModel):
    type: str
    coordinates: List[List[List[float]]]

    @validator("coordinates")
    def must_have_exactly_five_coordinates(cls, coordinates_value):
        for polygon in coordinates_value:
            if len(polygon) != 5:
                raise ValueError("Polygon must have exactly 5 coordinate pairs")
            if polygon[0] != polygon[-1]:
                raise ValueError(
                    "The first and last coordinate pairs must be the same to form a closed polygon"
                )
        return coordinates_value

    @validator("type")
    def type_must_be_polygon(cls, type_value):
        if type_value != "Polygon":
            raise ValueError("Geometry must be a Polygon")
        return type_value


class GeoJSONFeature(BaseModel):
    type: str
    geometry: CustomPolygon
    properties: dict


router = APIRouter()


@router.post("/prediction-request")
async def create_geojson_feature():
    # async def create_geojson_feature(feature: GeoJSONFeature):
    query_sh_catalog(
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [35.51974484135931, -21.512226110929063],
                    [35.51974484135931, -36.62666431275848],
                    [54.49896668354583, -36.62666431275848],
                    [54.49896668354583, -21.512226110929063],
                    [35.51974484135931, -21.512226110929063],
                ]
            ],
        },
        "2024-03-18T00:00:00Z/2024-03-20T23:59:59Z",
    )
    return {"message": "GeoJSON feature received", "feature": "NONE"}
