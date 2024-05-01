import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_predictions_with_invalid_query():
    response = client.get("/predictions?limit=Hello")
    assert response.status_code == 422


def test_get_predictions():
    limit = 6  # This is the limit of the number of predictions to be returned
    response = client.get(f"/predictions?limit={limit}")
    assert response.status_code == 200
    data = json.loads(
        response.json()
    )  # Manually parse the JSON string to a Python dict
    assert "type" in data and data["type"] == "FeatureCollection"
    assert "features" in data and isinstance(data["features"], list)
    assert len(data["features"]) == limit
    for feature in data["features"]:
        assert "type" in feature and feature["type"] == "Feature"
        assert "properties" in feature and isinstance(feature["properties"], dict)
        assert "pixelValue" in feature["properties"] and isinstance(
            feature["properties"]["pixelValue"], int
        )
        assert 0 <= feature["properties"]["pixelValue"] <= 255
        assert "geometry" in feature and isinstance(feature["geometry"], dict)
        assert (
            "type" in feature["geometry"] and feature["geometry"]["type"] == "Polygon"
        )
        assert "coordinates" in feature["geometry"] and isinstance(
            feature["geometry"]["coordinates"], list
        )
        assert len(feature["geometry"]["coordinates"][0]) == 5
        for coordinate in feature["geometry"]["coordinates"]:
            coordinate = coordinate[0]  # Unpack the list of coordinates
            assert isinstance(coordinate, list)
            assert len(coordinate) == 2
            assert isinstance(coordinate[0], float)
            assert isinstance(coordinate[1], float)
