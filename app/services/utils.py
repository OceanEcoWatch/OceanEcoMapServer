import geopandas as gpd
import pyproj
from shapely.geometry import Polygon, box
from pyproj.database import query_utm_crs_info
from pyproj.aoi import AreaOfInterest
from app.types.helpers import BoundingBox


def is_covering_bbox(inner_bbox_list, outer_bbox_list) -> bool:
    # Define your bounding boxes
    # Example: box(minx, miny, maxx, maxy)
    inner_box = box(*inner_bbox_list)
    outer_box = box(*outer_bbox_list)
    # Create GeoSeries
    inner_geoSeries = gpd.GeoSeries([inner_box])
    outer_geoSeries = gpd.GeoSeries([outer_box])

    # Check if bbox2 is within bbox1
    is_within = outer_geoSeries.contains(inner_geoSeries)[0]  # type: ignore

    print(f"is within:{is_within}")
    return is_within


# # a in b
# is_covering_bbox([1, 1, 2, 2], [0, 0, 3, 3])

# # b in a
# is_covering_bbox([0, 0, 3, 3], [1, 1, 2, 2])

# # a == b
# is_covering_bbox([0, 0, 3, 3], [0, 0, 3, 3])

# # a is in b, but they have one border in common
# is_covering_bbox([1, 1, 3, 3], [1, 0, 4, 4])


def intersecting_polygons(base_polygon, intersec_polygon):
    base_polygon = Polygon(base_polygon)
    intersec_polygon = Polygon(intersec_polygon)
    return base_polygon.intersects(intersec_polygon)


# def polygons_to_geoJson(polygons: list[Polygon]):
#     # Convert Shapely polygons to GeoJSON format
#     features = []
#     for polygon in polygons:
#         features.append(
#             {
#                 "type": "Feature",
#                 "properties": {},  # Add properties here as needed, e.g., ids, timestamps
#                 "geometry": json.loads(json.dumps(shapely.geometry.mapping(polygon))),
#             }
#         )

#     geojson = {"type": "FeatureCollection", "features": features}


def parse_bbox(bbox_str: str) -> BoundingBox:
    """
    Parses a bounding box string and returns a BoundingBox named tuple.

    Args:
    bbox_str (str): A comma-separated string with four coordinates in the order of
                    min longitude, min latitude, max longitude, max latitude.

    Returns:
    BoundingBox: A named tuple containing the bounding box coordinates as floats.

    Raises:
    ValueError: If the input string is incorrectly formatted or cannot be converted to floats.
    """
    try:
        parts = bbox_str.split(",")
        if len(parts) != 4:
            raise ValueError(
                "Bounding box string must contain exactly four comma-separated values."
            )

        min_x, min_y, max_x, max_y = map(
            float, parts)  # Converts each part to float

        return BoundingBox(min_x, min_y, max_x, max_y)
    except ValueError as e:
        raise ValueError(f"Error parsing bounding box: {str(e)}")
        raise ValueError(f"Error parsing bounding box: {str(e)}")


def determine_utm_epsg(  # thanks to marc for this function :D
    source_epsg: int,
    west_lon: float,
    south_lat: float,
    east_lon: float,
    north_lat: float,
    contains: bool = True,
) -> int:
    """
    Determine the UTM EPSG code for a given epsg code and bounding box

    :param source_epsg: The source EPSG code
    :param west_lon: The western longitude
    :param south_lat: The southern latitude
    :param east_lon: The eastern longitude
    :param north_lat: The northern latitude
    :param contains: If True, the UTM CRS must contain the bounding box,
        if False, the UTM CRS must intersect the bounding box.

    :return: The UTM EPSG code

    :raises ValueError: If no UTM CRS is found for the epsg and bbox
    """
    datum_name = pyproj.CRS.from_epsg(source_epsg).to_dict()["datum"]

    utm_crs_info = query_utm_crs_info(
        datum_name=datum_name,
        area_of_interest=AreaOfInterest(
            west_lon, south_lat, east_lon, north_lat),
        contains=contains,
    )

    if not utm_crs_info:
        raise ValueError(
            f"No UTM CRS found for the datum {datum_name} and bbox")

    return int(utm_crs_info[0].code)


def is_utm_epsg(epsg: int) -> bool:
    """Check if an EPSG code is a UTM code."""
    return pyproj.CRS.from_epsg(epsg).to_dict()["proj"] == "utm"


def get_bounding_box(polygon_coords, epsgCode: int = 4326):
    """
    Given a list of polygon coordinates, return the bounding box that perfectly surrounds the polygon.

    :param polygon_coords: List of tuples representing the coordinates of the polygon.
    :return: Tuple containing the bounding box in the format (minx, miny, maxx, maxy).
    """
    # Create the polygon from the provided coordinates
    polygon = Polygon(polygon_coords)

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(
        index=[0], crs=f"EPSG:{str(epsgCode)}", geometry=[polygon])

    # Get the bounding box
    bbox = gdf.total_bounds

    return bbox
