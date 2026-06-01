from typing import Any

from fastapi.testclient import TestClient
from httpx import Response

from app.schemas import DeviceOut


def create_device(client: TestClient, name: str = "pump", state: str = "off") -> Response:
    return client.post(
        "/devices",
        json={"name": name, "state": state},
    )


def test_post_devices_returns_created_id(client: TestClient) -> None:
    response: Response = create_device(client, "pump", "off")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "device created"
    assert body["data"]["id"] > 0


def test_post_devices_rejects_missing_name(client: TestClient) -> None:
    response: Response = client.post("/devices", json={"state": "off"})
    assert response.status_code == 422


def test_post_devices_rejects_missing_state(client: TestClient) -> None:
    response: Response = client.post("/devices", json={"name": "pump"})
    assert response.status_code == 422


def test_get_devices_returns_all_devices_in_descending_order(client: TestClient) -> None:
    create_device(client, "pump", "off")
    create_device(client, "fan", "off")
    create_device(client, "sprinkler", "on")

    response: Response = client.get("/devices")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 3

    items: list[DeviceOut] = [DeviceOut(**item) for item in body["data"]]
    ids: list[int] = [item.id for item in items]
    assert ids == sorted(ids, reverse=True)
    assert {item.name for item in items} == {"pump", "fan", "sprinkler"}


def test_get_devices_filters_by_name(client: TestClient) -> None:
    create_device(client, "pump", "off")
    create_device(client, "fan", "off")

    response: Response = client.get("/devices", params={"name": "fan"})
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert len(body["data"]) == 1
    device: DeviceOut = DeviceOut(**body["data"][0])
    assert device.name == "fan"
    assert device.state == "off"


def test_get_devices_limit_returns_up_to_limit(client: TestClient) -> None:
    create_device(client, "pump", "off")
    create_device(client, "fan", "off")
    create_device(client, "sprinkler", "on")

    response: Response = client.get("/devices", params={"limit": 2})
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert len(body["data"]) == 2


def test_get_devices_by_name_returns_device(client: TestClient) -> None:
    create_device(client, "pump", "off")

    response: Response = client.get("/devices/pump")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    device: DeviceOut = DeviceOut(**body["data"])
    assert device.name == "pump"
    assert device.state == "off"


def test_get_devices_by_name_returns_404_for_missing_device(client: TestClient) -> None:
    response: Response = client.get("/devices/nonexistent")
    assert response.status_code == 404


def test_post_device_state_updates_device_state(client: TestClient) -> None:
    create_device(client, "pump", "off")

    response: Response = client.post("/devices/pump/state", json={"state": "on"})
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "state updated"
    updated: DeviceOut = DeviceOut(**body["data"])
    assert updated.name == "pump"
    assert updated.state == "ON"


def test_post_device_state_rejects_invalid_state(client: TestClient) -> None:
    create_device(client, "pump", "off")

    response: Response = client.post("/devices/pump/state", json={"state": "notastate"})
    assert response.status_code == 400


def test_post_device_state_returns_404_for_unknown_device(client: TestClient) -> None:
    response: Response = client.post("/devices/ghost/state", json={"state": "on"})
    assert response.status_code == 404


def test_post_devices_rejects_duplicate_name(client: TestClient) -> None:
    first: Response = create_device(client, "pump", "off")
    assert first.status_code == 200

    duplicate: Response = create_device(client, "pump", "off")
    assert duplicate.status_code == 400


def test_get_devices_limit_validation_rejects_invalid_values(client: TestClient) -> None:
    for invalid_limit in [0, 100, -5]:
        response: Response = client.get("/devices", params={"limit": invalid_limit})
        assert response.status_code == 400