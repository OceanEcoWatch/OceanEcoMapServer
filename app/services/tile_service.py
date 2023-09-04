import morecantile

from app.core.request import TileCoords


def get_bbox_from_tile_coords(tile_coords: TileCoords) -> tuple[float, float, float, float]:
    tms = morecantile.tms.get("WebMercatorQuad")
    bounds = tms.bounds(morecantile.Tile(**tile_coords.dict()))

    return bounds.left, bounds.bottom, bounds.right, bounds.top
