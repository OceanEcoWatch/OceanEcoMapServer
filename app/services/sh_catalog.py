from sentinelhub import CRS, Geometry, SentinelHubCatalog, SHConfig

from app.config.config import SENTINAL_HUB


def query_sh_catalog(geometry: dict):
    config = SHConfig()
    config.instance_id = SENTINAL_HUB["INSTANCE_ID"]
    config.sh_client_id = SENTINAL_HUB["CLIENT_ID"]
    config.sh_client_secret = SENTINAL_HUB["CLIENT_SECRET"]

    catalog = SentinelHubCatalog(config=config)

    # Define the search area as a Polygon GeoJSON
    search_area = Geometry(
        geometry=geometry,
        crs=CRS.WGS84,
    )

    # Perform the search
    search_results = catalog.search(
        collection="sentinel-2-l2a",
        geometry=search_area,
        limit=20,
        datetime="2024-03-01T00:00:00Z/2024-03-20T23:59:59Z",
    )

    print(search_results)
    # Print out the IDs of found items
    for item in search_results:
        print(f"ID: {item['id']}")
        print(f"bbox: {item['bbox']}")
        print(f"timestamp: {item['properties']['datetime']}")

    # # Optionally, save the found items to a GeoJSON file
    # catalog.save_search_result(search_results, "search_results.geojson")
    # catalog.save_search_result(search_results, "search_results.geojson")
