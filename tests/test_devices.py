from app.models import DeviceOut


def create_device(client, name="pump", state="off"):
    return client.post(
        "/devices",
        json={"name": name, "state": state},
    )


def test_post_devices_returns_created_id(client):
    response = create_device(client, "pump", "off")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "device created"
    assert "data" in body and "id" in body["data"]


def test_get_devices_returns_all_created_devices(client):
    create_device(client, "pump", "off")
    create_device(client, "fan", "off")

    response = client.get("/devices")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["data"], list)
    names = {device["name"] for device in body["data"]}
    assert {"pump", "fan"}.issubset(names)


def test_get_devices_filters_by_name(client):
    create_device(client, "pump", "off")
    create_device(client, "fan", "off")

    response = client.get("/devices", params={"name": "fan"})
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "fan"


def test_get_devices_by_name_returns_device(client):
    create_device(client, "pump", "off")

    response = client.get("/devices/pump")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    device = DeviceOut(**body["data"])
    assert device.name == "pump"
    assert device.state == "off"


def test_get_devices_by_name_returns_404_for_missing_device(client):
    response = client.get("/devices/nonexistent")
    assert response.status_code == 404


def test_post_devices_state_updates_device_state(client):
    create_device(client, "pump", "off")

    response = client.post("/devices/pump/state", params={"state": "on"})
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "state updated"
    assert body["data"]["state"] == "ON"


def test_post_devices_state_rejects_invalid_state(client):
    create_device(client, "pump", "off")

    response = client.post("/devices/pump/state", params={"state": "notastate"})
    assert response.status_code == 400


def test_post_devices_rejects_duplicate_name(client):
    first = create_device(client, "pump", "off")
    assert first.status_code == 200

    duplicate = create_device(client, "pump", "off")
    assert duplicate.status_code == 400


def test_get_devices_limit_validation_rejects_invalid_values(client):
    for invalid_limit in [0, 100, -5]:
        response = client.get("/devices", params={"limit": invalid_limit})
        assert response.status_code == 400
