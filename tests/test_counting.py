import io


def test_get_counts_returns_structure(client):
    resp = client.get("/api/v1/counting/counts", params={"camera_id": "cam1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["camera_id"] == "cam1"
    assert isinstance(data["zone_counts"], list)
    assert isinstance(data["line_counts"], list)
    assert isinstance(data["total_unique_objects"], int)


def test_get_counts_grows_on_repeated_calls(client):
    r1 = client.get("/api/v1/counting/counts", params={"camera_id": "cam1"}).json()
    r2 = client.get("/api/v1/counting/counts", params={"camera_id": "cam1"}).json()
    assert r2["total_unique_objects"] >= r1["total_unique_objects"]


def test_all_counts_empty(client):
    resp = client.get("/api/v1/counting/all_counts")
    assert resp.status_code == 200
    assert resp.json()["total_cameras"] == 0


def test_all_counts_after_adding_cameras(client):
    client.post("/api/v1/cameras/", params={"camera_id": "cam1"})
    client.post("/api/v1/cameras/", params={"camera_id": "cam2"})
    resp = client.get("/api/v1/counting/all_counts")
    assert resp.json()["total_cameras"] == 2


def test_events_empty(client):
    resp = client.get("/api/v1/counting/events")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_events_populated_after_tracking(client):
    client.post(
        "/api/v1/tracking/track_frame",
        params={"camera_id": "cam1"},
        files={"file": ("f.jpg", io.BytesIO(b"x"), "image/jpeg")},
    )
    resp = client.get("/api/v1/counting/events")
    assert resp.json()["count"] >= 2


def test_events_camera_filter(client):
    client.post(
        "/api/v1/tracking/track_frame",
        params={"camera_id": "cam1"},
        files={"file": ("f.jpg", io.BytesIO(b"x"), "image/jpeg")},
    )
    resp = client.get("/api/v1/counting/events", params={"camera_id": "cam2"})
    assert resp.json()["count"] == 0


def test_roi_density(client):
    resp = client.get("/api/v1/counting/roi_density/cam1/zone_a")
    assert resp.status_code == 200
    data = resp.json()
    assert "current_count" in data
    assert "average_density_30frames" in data


def test_reset_counts(client):
    client.get("/api/v1/counting/counts", params={"camera_id": "cam1"})
    client.post("/api/v1/counting/reset_counts", params={"camera_id": "cam1"})
    from api.mock_state import state
    assert "cam1" not in state.counts


def test_counting_statistics(client):
    resp = client.get("/api/v1/counting/statistics")
    assert resp.status_code == 200
