from fastapi.testclient import TestClient
from httpx import Response


def test_health(client: TestClient) -> None:
    response: Response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
