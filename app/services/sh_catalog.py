import itertools
from datetime import datetime
from typing import Any, Dict, List

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
from sentinelhub.api.catalog import SentinelHubCatalog
from sentinelhub.config import SHConfig
from sentinelhub.constants import CRS
from sentinelhub.geometry import Geometry
from shapely.geometry import MultiPolygon, Polygon, box

from app.config.config import SENTINAL_HUB


def query_sh_catalog(aoi: dict, time_range: str):
    LIMIT = 100  # upper bound is 100 (SH limitation)
    aoi_poly = Polygon(aoi["coordinates"][0])

    search_iterator = get_iterator_for_shCatalog_l2a_query(100, aoi, time_range, 50)

    catalog_item_list = get_item_list_from_iterator(search_iterator, aoi_poly, LIMIT)
    catalog_item_list.sort(key=lambda x: x["coverage"], reverse=True)

    # pprint.pp(catalog_item_list)
    # print(f"number of items in catalog_item_list: {len(catalog_item_list)}")

    # Create a GeoDataFrame from the catalog_item_list
    gdf = gpd.GeoDataFrame(
        data=catalog_item_list, geometry="multi_polygon", crs="WGS84"
    )  # type: ignore

    # make geoDataFrame from the target aoi
    gdf_outline = gpd.GeoDataFrame(
        [{"id": "aoi", "geometry": aoi_poly}], geometry="geometry", crs="WGS84"
    )  # type: ignore

    catalog_item_list.sort(key=lambda x: x["coverage"], reverse=True)
    # pprint.pp(catalog_item_list)
    # print(f"number of items in catalog_item_list: {len(catalog_item_list)}")

    visualize_coverage_as_png(gdf, gdf_outline, show_plot=True)
    visualize_coverage_as_html_map(gdf, gdf_outline)

    solutions = []

    return

    for item in catalog_item_list:
        if item["coverage"] >= 1:
            # remove item from list and put it in solutions
            solutions.append(item)
            catalog_item_list.remove(item)

    print("after filtering out all fully covered items")
    print(f"number of solutions: {len(solutions)}")

    catalog_item_combinations = []
    combination_possibilities = []
    # pairs
    combination_possibilities = combination_possibilities + get_list_of_combinations(
        catalog_item_list, 2
    )
    # triplets
    combination_possibilities = combination_possibilities + get_list_of_combinations(
        catalog_item_list, 3
    )
    # quadruplets
    combination_possibilities = combination_possibilities + get_list_of_combinations(
        catalog_item_list, 4
    )

    print(f"number of combination_possibilities: {len(combination_possibilities)}")

    for combination in combination_possibilities:
        ids = [item["ids"] for item in combination]
        coverage = get_area_coverage(
            aoi_poly, [item["geometries"] for item in combination]
        )
        timestamps = [item["timestamps"] for item in combination]
        cloud_covers = [item["cloud_covers"] for item in combination]
        geometries = [item["geometries"] for item in combination]
        catalog_item_combinations.append(
            {
                "ids": ids,
                "coverage": coverage,
                "timestamps": timestamps,
                "cloud_covers": cloud_covers,
                "geometries": geometries,
            }
        )

    catalog_item_combinations.sort(key=lambda x: x["coverage"], reverse=True)
    print("all combinations are applied, and sorted by coverage")

    print(catalog_item_combinations[0:3])

    # # Optionally, save the found items to a GeoJSON file
    # catalog.save_search_result(search_results, "search_results.geojson")
    # catalog.save_search_result(search_results, "search_results.geojson")


def generate_all_combinations(catalog_item_list: List[Dict[str, Any]]):
    all_combinations = []
    for r in range(1, len(catalog_item_list) + 1):
        combinations_object = itertools.combinations(catalog_item_list, r)
        all_combinations.extend(list(combinations_object))
    # print(f"number of unique items in list: {len(catalog_item_list)}")
    # print(f"number of all combinations: {len(all_combinations)}")

    return all_combinations


def calculate_geometry_score():
    pass
    # calculate geometry score
    # per combination
    # per every element
    # go through every evelemt of


def get_area_coverage(area_to_cover: Polygon, geometries: List[Polygon]):
    # print type of the inputs
    print(f"type of area_to_cover: {type(area_to_cover)}")
    print(f"type of geometries: {type(geometries)}")

    geometry = gpd.GeoSeries(geometries)
    area_to_cover = gpd.GeoSeries([area_to_cover])  # type: ignore

    intersection = area_to_cover.intersection(geometry.unary_union)  # type: ignore
    intersection_area = intersection.area.iloc[0]
    area_to_cover_area = area_to_cover.area.iloc[0]  # type: ignore
    coverage = intersection_area / area_to_cover_area
    print(f"coverage: {coverage}")
    return coverage


def get_list_of_combinations(lst: List[dict], combination_size: int):
    return list(itertools.combinations(lst, combination_size))  # type: ignore


# def score_catalog_items():

#     cloud_weight = 1
#     time_weight = 1
#     geometry_weight = 1


#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry


#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry


#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry

#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry

#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry
#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry
#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry
#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry
#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry
#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry
#     score = cloud_weight * cloud_cover + time_weight * time + geometry_weight * geometry


def get_iterator_for_shCatalog_l2a_query(
    limit: int, aoi: dict, time_range: str, cloud_cover_filter_lt: int
):
    config = SHConfig()
    config.instance_id = SENTINAL_HUB["INSTANCE_ID"]
    config.sh_client_id = SENTINAL_HUB["CLIENT_ID"]
    config.sh_client_secret = SENTINAL_HUB["CLIENT_SECRET"]

    catalog = SentinelHubCatalog(config=config)

    # Define the search area as a Polygon GeoJSON
    sh_aoi_geometry = Geometry(
        geometry=aoi,
        crs=CRS.WGS84,
    )

    # Perform the search
    search_result_iterator = catalog.search(
        collection="sentinel-2-l2a",
        geometry=sh_aoi_geometry,
        limit=limit,
        datetime=time_range,
        filter=f"eo:cloud_cover <= {cloud_cover_filter_lt}",
        # sortby=[
        #     {"field": "eo:cloud_cover", "direction": "asc"}
        # ],  # Sort by cloud cover in ascending order
    )
    return search_result_iterator


def get_item_list_from_iterator(iterator, aoi_poly, LIMIT):
    count = 0
    catalog_item_list = []
    for item in iterator:
        count += 1
        # this manual counting is necessary because the CatalogSearchIterator does not have a length even though it limit is set to a value, the iterator will continue to the end of the catalog (which might be more than the limit)
        if count > LIMIT:
            print(
                "WARNING! The limit for the CatalogSearchIterator is reached! The rest of the items will be ignored."
            )
            break
        geometry = box(*item["bbox"])
        catalog_item = {
            "id": item["id"],
            "ids": [item["id"]],
            "parsedDate": datetime.strptime(
                item["properties"]["datetime"], "%Y-%m-%dT%H:%M:%SZ"
            ).timestamp(),
            "timestamp": item["properties"]["datetime"],
            "timestamps": [item["properties"]["datetime"]],
            "cloud_covers": [item["properties"]["eo:cloud_cover"]],
            # "geometries": [geometry],  # Geometry added here
            "multi_polygon": MultiPolygon([geometry]),  # "geometry": "MultiPolygon"
            "coverage": get_area_coverage(aoi_poly, [geometry]),
        }

        # Append the dictionary to your list
        catalog_item_list.append(catalog_item)
    return catalog_item_list


def visualize_coverage_as_png(gdf_data, gdf_outline, show_plot=False):
    # visualize how the aoi is covered by the catalog items and save to file and html
    plot_axis = gdf_data.plot(
        column="parsedDate",
        categorical=True,
        scheme="EqualInterval",
        k=5,
        legend=True,
        legend_kwds={"loc": "lower right"},
    )
    gdf_data.boundary.plot(ax=plot_axis, color="red", linewidth=0.5)
    gdf_outline.boundary.plot(ax=plot_axis, color="black", linewidth=1)
    # Save the plot to a file

    plt.savefig("plot.png", dpi=300, bbox_inches="tight")
    if show_plot:
        plt.show()
    return


def visualize_coverage_as_html_map(
    gdf_data,
    gdf_outline,
):
    # Convert the GeoDataFrame to GeoJSON
    gdf_geojson = gdf_data.to_json()

    # Create a map object centered around the mean of your GeoDataFrame's geometries
    m = folium.Map(
        location=[
            gdf_data.geometry.centroid.y.mean(),
            gdf_data.geometry.centroid.x.mean(),
        ],
        zoom_start=8,
    )

    # Add the GeoJSON layer to the map
    folium.GeoJson(gdf_geojson, name="geodataframe").add_to(m)

    # Save the map
    m.save("my_map.html")
    # Save the map
    m.save("my_map.html")
