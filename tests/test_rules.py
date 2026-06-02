from typing import Any

from fastapi.testclient import TestClient
from httpx import Response


def create_sensor(client: TestClient, name: str = "pump", state: str = "off") -> Response:
    return client.post(
        "/sensors",
        json={"name": name, "state": state},
    )


def create_rule(client: TestClient, name: str = "fan_control", enabled: bool = True) -> Response:
    return client.post(
        "/rules",
        json={
            "name": name,
            "enabled": enabled,
            "condition_type": "measurement_threshold",
            "condition_measurement": "temperature",
            "condition_operator": ">",
            "condition_value": 25,
            "action_type": "set_sensor_state",
            "action_sensor": "fan",
            "action_state": "ON",
        },
    )


def test_post_rules_creates_rule(client: TestClient) -> None:
    create_sensor(client, "fan", "off")

    response: Response = create_rule(client, "fan_control")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "rule created"
    assert body["data"]["id"] > 0


def test_get_rules_returns_created_rule(client: TestClient) -> None:
    create_sensor(client, "fan", "off")
    create_rule(client, "fan_control")

    response: Response = client.get("/rules")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "fan_control"
    assert body["data"][0]["enabled"] is True


def test_get_rule_by_name_returns_rule(client: TestClient) -> None:
    create_sensor(client, "fan", "off")
    create_rule(client, "fan_control")

    response: Response = client.get("/rules/fan_control")
    assert response.status_code == 200

    body: dict[str, Any] = response.json()
    assert body["status"] == "ok"
    assert body["data"]["name"] == "fan_control"
    assert body["data"]["condition_measurement"] == "temperature"
    assert body["data"]["action_sensor"] == "fan"


def test_disable_rule_prevents_automation(client: TestClient) -> None:
    create_sensor(client, "fan", "off")
    create_rule(client, "fan_control")

    response: Response = client.post("/rules/fan_control/toggle", json={"enabled": False})
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["data"]["enabled"] is False

    measure: Response = client.post(
        "/measurements",
        json={"source": "sensor", "name": "temperature", "value": 27.0, "unit": "C"},
    )
    assert measure.status_code == 200

    sensor_response: Response = client.get("/sensors/fan")
    assert sensor_response.status_code == 200
    sensor_body: dict[str, Any] = sensor_response.json()
    assert sensor_body["data"]["state"] == "OFF"


def test_measurement_triggers_enabled_rule(client: TestClient) -> None:
    create_sensor(client, "fan", "off")
    create_rule(client, "fan_control")

    response: Response = client.post(
        "/measurements",
        json={"source": "sensor", "name": "temperature", "value": 27.0, "unit": "C"},
    )
    assert response.status_code == 200

    sensor_response: Response = client.get("/sensors/fan")
    assert sensor_response.status_code == 200
    sensor_body: dict[str, Any] = sensor_response.json()
    assert sensor_body["data"]["state"] == "ON"


def test_delete_rule_removes_it(client: TestClient) -> None:
    create_sensor(client, "fan", "off")
    create_rule(client, "fan_control")

    delete_response: Response = client.delete("/rules/fan_control")
    assert delete_response.status_code == 200

    body: dict[str, Any] = delete_response.json()
    assert body["status"] == "ok"
    assert body["message"] == "rule fan_control deleted"

    missing_response: Response = client.get("/rules/fan_control")
    assert missing_response.status_code == 404
