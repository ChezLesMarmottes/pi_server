from typing import Any

from fastapi.testclient import TestClient
from httpx import Response

from app.schemas import MeasurementOut


def create_measurement(
    client: TestClient,
    source: str = "sensor",
    name: str = "temperature",
    value: float = 22.5,
    unit: str | None = "C",
) -> Response:
    payload: dict[str, Any] = {"source": source, "name": name, "value": value}
    if unit is not None:
        payload["unit"] = unit
    return client.post("/measurements", json=payload)


def test_post_measurements_returns_created_id(client: TestClient) -> None:
    response: Response = create_measurement(client, "sensor-1", "humidity", 55.0, "%")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "measurement stored"
    assert body["data"]["id"] > 0


def test_post_measurements_rejects_missing_source(client: TestClient) -> None:
    response: Response = client.post("/measurements", json={"name": "temperature", "value": 20.0})
    assert response.status_code == 422


def test_post_measurements_rejects_missing_name(client: TestClient) -> None:
    response: Response = client.post("/measurements", json={"source": "sensor", "value": 20.0})
    assert response.status_code == 422


def test_post_measurements_accepts_missing_unit(client: TestClient) -> None:
    response: Response = create_measurement(client, source="sensor-1", name="humidity", value=55.0, unit=None)
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"


def test_get_measurements_returns_records_in_descending_order(client: TestClient) -> None:
    create_measurement(client, "sensor-a", "temperature", 18.2, "C")
    create_measurement(client, "sensor-b", "humidity", 60.3, "%")
    create_measurement(client, "sensor-c", "pressure", 1012.4, "hPa")

    response: Response = client.get("/measurements")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 3

    items: list[MeasurementOut] = [MeasurementOut(**item) for item in body["data"]]
    ids: list[int] = [item.id for item in items]
    assert ids == sorted(ids, reverse=True)


def test_get_measurements_filters_by_name(client: TestClient) -> None:
    create_measurement(client, "sensor-a", "temperature", 18.2, "C")
    create_measurement(client, "sensor-b", "humidity", 60.3, "%")
    create_measurement(client, "sensor-c", "temperature", 19.1, "C")

    response: Response = client.get("/measurements", params={"name": "temperature"})
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert len(body["data"]) == 2

    values: list[float] = [item["value"] for item in body["data"]]
    assert values == sorted(values, reverse=True)
    assert all(item["name"] == "temperature" for item in body["data"])


def test_get_measurements_limit_returns_up_to_limit(client: TestClient) -> None:
    create_measurement(client, "sensor-a", "temperature", 18.2, "C")
    create_measurement(client, "sensor-b", "humidity", 60.3, "%")
    create_measurement(client, "sensor-c", "pressure", 1012.4, "hPa")

    response: Response = client.get("/measurements", params={"limit": 2})
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert len(body["data"]) == 2


def test_get_measurements_limit_validation_rejects_invalid_values(client: TestClient) -> None:
    for invalid_limit in [0, 100, -1]:
        response: Response = client.get("/measurements", params={"limit": invalid_limit})
        assert response.status_code == 400


def test_get_measurements_returns_empty_for_unknown_name(client: TestClient) -> None:
    create_measurement(client, "sensor-a", "temperature", 18.2, "C")

    response: Response = client.get("/measurements", params={"name": "unknown"})
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert body["data"] == []


def test_get_measurements_latest_returns_latest_by_name(client: TestClient) -> None:
    create_measurement(client, "sensor-1", "temperature", 20.0, "C")
    create_measurement(client, "sensor-1", "temperature", 21.5, "C")
    create_measurement(client, "sensor-2", "humidity", 55.0, "%")
    create_measurement(client, "sensor-2", "humidity", 56.0, "%")
    create_measurement(client, "sensor-3", "pressure", 1012.4, "hPa")

    response: Response = client.get("/measurements/latest")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 3

    latest_by_name: dict[str, dict[str, Any]] = {item["name"]: item for item in body["data"]}
    assert latest_by_name["temperature"]["value"] == 21.5
    assert latest_by_name["humidity"]["value"] == 56.0
    assert latest_by_name["pressure"]["value"] == 1012.4


def test_post_measurements_rejects_invalid_payload(client: TestClient) -> None:
    missing_fields: Response = client.post("/measurements", json={"source": "sensor"})
    assert missing_fields.status_code == 422

    invalid_value: Response = client.post(
        "/measurements",
        json={"source": "sensor", "name": "temperature", "value": "not-a-number", "unit": "C"},
    )
    assert invalid_value.status_code == 422
