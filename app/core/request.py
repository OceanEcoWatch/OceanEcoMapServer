from pydantic import BaseModel


class TileCoords(BaseModel):
    x: int
    y: int
    z: int
