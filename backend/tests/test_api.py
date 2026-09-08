from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-request-id"]
    assert response.headers["cache-control"] == "no-store"


def test_missing_database_is_not_zero(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert client.get("/api/ready").status_code == 503
    data = client.get("/api/system").json()
    assert data["database"]["status"] == "not_configured"
    assert data["counts"] is None
    assert data["datasets"] == []


def test_pagination_rejects_invalid_values():
    for query in ["page=0", "page_size=101", "page_size=-1", "q=" + "a" * 81]:
        assert client.get("/api/genes?" + query).status_code == 422
