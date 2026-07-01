from fastapi.testclient import TestClient

from bujji.api.server import app

client = TestClient(app)


class TestAPI:
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "BUJJI"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"

    def test_chat_no_message(self):
        response = client.post("/chat", json={})
        assert response.status_code == 422

    def test_plan_no_task(self):
        response = client.post("/plan", json={})
        assert response.status_code == 422

    def test_memory_store_invalid(self):
        response = client.post(
            "/memory/store",
            json={},
        )
        assert response.status_code == 422

    def test_openapi_schema(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "BUJJI API"
        assert schema["info"]["version"] == "1.0.0"
