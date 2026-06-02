from typing import Any

from fastapi.testclient import TestClient
from httpx import Response

from app.schemas import SensorOut


def create_sensor(client: TestClient, name: str = "pump", state: str = "off") -> Response:
    return client.post(
        "/sensors",
        json={"name": name, "state": state},
    )


def test_post_sensors_returns_created_id(client: TestClient) -> None:
    response: Response = create_sensor(client, "pump", "off")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "sensor created"
    assert body["data"]["id"] > 0


def test_post_sensors_rejects_missing_name(client: TestClient) -> None:
    response: Response = client.post("/sensors", json={"state": "off"})
    assert response.status_code == 422


def test_post_sensors_rejects_missing_state(client: TestClient) -> None:
    response: Response = client.post("/sensors", json={"name": "pump"})
    assert response.status_code == 422


def test_get_sensors_returns_all_sensors_in_descending_order(client: TestClient) -> None:
    create_sensor(client, "pump", "off")
    create_sensor(client, "fan", "off")
    create_sensor(client, "sprinkler", "on")

    response: Response = client.get("/sensors")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 3

    items: list[SensorOut] = [SensorOut(**item) for item in body["data"]]
    ids: list[int] = [item.id for item in items]
    assert ids == sorted(ids, reverse=True)
    assert {item.name for item in items} == {"pump", "fan", "sprinkler"}


def test_get_sensors_filters_by_name(client: TestClient) -> None:
    create_sensor(client, "pump", "off")
    create_sensor(client, "fan", "off")

    response: Response = client.get("/sensors", params={"name": "fan"})
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert len(body["data"]) == 1
    sensor: SensorOut = SensorOut(**body["data"][0])
    assert sensor.name == "fan"
    assert sensor.state == "off"


def test_get_sensors_limit_returns_up_to_limit(client: TestClient) -> None:
    create_sensor(client, "pump", "off")
    create_sensor(client, "fan", "off")
    create_sensor(client, "sprinkler", "on")

    response: Response = client.get("/sensors", params={"limit": 2})
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert len(body["data"]) == 2


def test_get_sensors_by_name_returns_sensor(client: TestClient) -> None:
    create_sensor(client, "pump", "off")

    response: Response = client.get("/sensors/pump")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    sensor: SensorOut = SensorOut(**body["data"])
    assert sensor.name == "pump"
    assert sensor.state == "off"


def test_get_sensors_by_name_returns_404_for_missing_sensor(client: TestClient) -> None:
    response: Response = client.get("/sensors/nonexistent")
    assert response.status_code == 404


def test_post_sensor_state_updates_sensor_state(client: TestClient) -> None:
    create_sensor(client, "pump", "off")

    response: Response = client.post("/sensors/pump/state", json={"state": "on"})
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "state updated"
    updated: SensorOut = SensorOut(**body["data"])
    assert updated.name == "pump"
    assert updated.state == "ON"


def test_post_sensor_state_rejects_invalid_state(client: TestClient) -> None:
    create_sensor(client, "pump", "off")

    response: Response = client.post("/sensors/pump/state", json={"state": "notastate"})
    assert response.status_code == 422


def test_post_sensor_state_returns_404_for_unknown_sensor(client: TestClient) -> None:
    response: Response = client.post("/sensors/ghost/state", json={"state": "on"})
    assert response.status_code == 404


def test_post_sensors_rejects_duplicate_name(client: TestClient) -> None:
    first: Response = create_sensor(client, "pump", "off")
    assert first.status_code == 200

    duplicate: Response = create_sensor(client, "pump", "off")
    assert duplicate.status_code == 400


def test_get_sensors_limit_validation_rejects_invalid_values(client: TestClient) -> None:
    for invalid_limit in [0, 100, -5]:
        response: Response = client.get("/sensors", params={"limit": invalid_limit})
        assert response.status_code == 400