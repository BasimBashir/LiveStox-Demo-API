def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "ArkAI Tracking API"
    assert data["version"] == "1.0.0"
    assert "DEMO" in data["mode"]


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["uptime_seconds"] >= 0


def test_stats(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "tracking" in data
    assert "counting" in data
    assert "events" in data
