import geopandas as gpd
from shapely.geometry import Polygon, box


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


def intersecting_polygones(base_polygon, intersec_polygon):
    base_polygon = Polygon(base_polygon)
    intersec_polygon = Polygon(intersec_polygon)
    return base_polygon.intersects(intersec_polygon)


def polygons_to_geoJson(polygons: list[Polygon]):
    # Convert Shapely polygons to GeoJSON format
    features = []
    for polygon in polygons:
        features.append(
            {
                "type": "Feature",
                "properties": {},  # Add properties here as needed, e.g., ids, timestamps
                "geometry": json.loads(json.dumps(shapely.geometry.mapping(polygon))),
            }
        )

    geojson = {"type": "FeatureCollection", "features": features}
