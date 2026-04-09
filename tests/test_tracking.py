import io


def test_track_frame_returns_tracks(client):
    resp = client.post(
        "/api/v1/tracking/track_frame",
        params={"camera_id": "cam1"},
        files={"file": ("frame.jpg", io.BytesIO(b"fake"), "image/jpeg")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["camera_id"] == "cam1"
    assert 8 <= data["active_track_count"] <= 20
    assert len(data["tracks"]) == data["active_track_count"]
    t = data["tracks"][0]
    assert "track_id" in t
    assert len(t["bbox"]) == 4
    assert len(t["centroid"]) == 2
    assert 0.0 <= t["confidence"] <= 1.0


def test_track_frame_invalid_extension(client):
    resp = client.post(
        "/api/v1/tracking/track_frame",
        params={"camera_id": "cam1"},
        files={"file": ("frame.txt", io.BytesIO(b"bad"), "text/plain")},
    )
    assert resp.status_code == 400
    assert "Invalid file type" in resp.json()["detail"]


def test_active_tracks_empty_camera(client):
    resp = client.get("/api/v1/tracking/active_tracks", params={"camera_id": "cam1"})
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_active_tracks_populated_after_frame(client):
    client.post(
        "/api/v1/tracking/track_frame",
        params={"camera_id": "cam1"},
        files={"file": ("f.jpg", io.BytesIO(b"x"), "image/jpeg")},
    )
    resp = client.get("/api/v1/tracking/active_tracks", params={"camera_id": "cam1"})
    assert resp.json()["count"] >= 8


def test_active_tracks_all_cameras(client):
    for cam in ["cam1", "cam2"]:
        client.post(
            "/api/v1/tracking/track_frame",
            params={"camera_id": cam},
            files={"file": ("f.jpg", io.BytesIO(b"x"), "image/jpeg")},
        )
    resp = client.get("/api/v1/tracking/active_tracks")
    assert resp.json()["total_count"] >= 16


def test_track_info_not_found(client):
    resp = client.get("/api/v1/tracking/track_info/9999", params={"camera_id": "cam1"})
    assert resp.status_code == 404


def test_track_info_found(client):
    r = client.post(
        "/api/v1/tracking/track_frame",
        params={"camera_id": "cam1"},
        files={"file": ("f.jpg", io.BytesIO(b"x"), "image/jpeg")},
    )
    track_id = r.json()["tracks"][0]["track_id"]
    resp = client.get(f"/api/v1/tracking/track_info/{track_id}", params={"camera_id": "cam1"})
    assert resp.status_code == 200
    assert resp.json()["track_id"] == track_id


def test_reset_clears_tracks(client):
    client.post(
        "/api/v1/tracking/track_frame",
        params={"camera_id": "cam1"},
        files={"file": ("f.jpg", io.BytesIO(b"x"), "image/jpeg")},
    )
    client.post("/api/v1/tracking/reset/cam1")
    resp = client.get("/api/v1/tracking/active_tracks", params={"camera_id": "cam1"})
    assert resp.json()["count"] == 0


def test_statistics(client):
    resp = client.get("/api/v1/tracking/statistics")
    assert resp.status_code == 200
