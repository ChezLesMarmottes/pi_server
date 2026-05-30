from app.models import MeasurementOut


def create_measurement(client, source="sensor", name="temperature", value=22.5, unit="C"):
    return client.post(
        "/measurements",
        json={"source": source, "name": name, "value": value, "unit": unit},
    )


def test_post_measurements_returns_created_id(client):
    response = create_measurement(client, "sensor-1", "humidity", 55.0, "%")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "measurement stored"
    assert "data" in body and "id" in body["data"]


def test_get_measurements_returns_records_in_descending_order(client):
    create_measurement(client, "sensor-a", "temperature", 18.2, "C")
    create_measurement(client, "sensor-b", "humidity", 60.3, "%")

    response = client.get("/measurements")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 2

    ids = [item["id"] for item in body["data"]]
    assert ids == sorted(ids, reverse=True)


def test_get_measurements_filters_by_name(client):
    create_measurement(client, "sensor-a", "temperature", 18.2, "C")
    create_measurement(client, "sensor-b", "humidity", 60.3, "%")
    create_measurement(client, "sensor-c", "temperature", 19.1, "C")

    response = client.get("/measurements", params={"name": "temperature"})
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert len(body["data"]) == 2

    names = {item["name"] for item in body["data"]}
    assert names == {"temperature"}


def test_get_measurements_limit_validation_rejects_invalid_values(client):
    for invalid_limit in [0, 100, -1]:
        response = client.get("/measurements", params={"limit": invalid_limit})
        assert response.status_code == 400


def test_get_measurements_latest_returns_latest_by_name(client):
    create_measurement(client, "sensor-1", "temperature", 20.0, "C")
    create_measurement(client, "sensor-1", "temperature", 21.5, "C")
    create_measurement(client, "sensor-2", "humidity", 55.0, "%")
    create_measurement(client, "sensor-2", "humidity", 56.0, "%")
    create_measurement(client, "sensor-3", "pressure", 1012.4, "hPa")

    response = client.get("/measurements/latest")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 3

    latest_by_name = {item["name"]: item for item in body["data"]}
    assert latest_by_name["temperature"]["value"] == 21.5
    assert latest_by_name["humidity"]["value"] == 56.0
    assert latest_by_name["pressure"]["value"] == 1012.4


def test_post_measurements_rejects_invalid_payload(client):
    missing_fields = client.post("/measurements", json={"source": "sensor"})
    assert missing_fields.status_code == 422

    invalid_value = client.post(
        "/measurements",
        json={"source": "sensor", "name": "temperature", "value": "not-a-number", "unit": "C"},
    )
    assert invalid_value.status_code == 422
