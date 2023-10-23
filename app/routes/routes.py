from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import text

from app.core.request import TileCoords
from app.db.connect import create_db_session, safe_execute_query
from app.services.tile_service import get_bbox_from_tile_coords
router = APIRouter()


@router.get("/{datetime}/tile/{z}/{x}/{y}.png", tags=["Tiles"],
            response_class=Response,
            responses={200: {"content": {"image/png": {}}}})
def get_tile(datetime: str, tile_coords: TileCoords = Depends()):
    aoi_bbox = get_bbox_from_tile_coords(tile_coords)
    # todo: retrive tile data from db
    # tile = get_tile_data(tile_coords, datetime)
    # todo render tile in a png image
    # image_content = render_tile(tile)
    #
    # return Response(
    #     status_code=200,
    #     content=image_content,
    #     media_type="image/png"
    # )
    return {"message": "Hello World"}

@router.get("/test")        
def get_test():
    
    db_session = create_db_session()
    testData= safe_execute_query(db_session, text("SELECT * FROM prediction_rasters"))
    db_session.close()
    return {"test": testData }