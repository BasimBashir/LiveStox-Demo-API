def test_list_cameras_empty(client):
    resp = client.get("/api/v1/cameras/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_add_camera(client):
    resp = client.post("/api/v1/cameras/", params={"camera_id": "cam1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["camera"]["camera_id"] == "cam1"
    assert data["camera"]["status"] == "inactive"


def test_add_duplicate_camera(client):
    client.post("/api/v1/cameras/", params={"camera_id": "cam1"})
    resp = client.post("/api/v1/cameras/", params={"camera_id": "cam1"})
    assert resp.status_code == 400


def test_list_cameras_after_add(client):
    client.post("/api/v1/cameras/", params={"camera_id": "cam1"})
    client.post("/api/v1/cameras/", params={"camera_id": "cam2"})
    resp = client.get("/api/v1/cameras/")
    assert resp.json()["total"] == 2


def test_update_rtsp(cam_client):
    resp = cam_client.put(
        "/api/v1/cameras/cam1",
        json={"rtsp_url": "rtsp://192.168.1.1/stream"},
    )
    assert resp.status_code == 200
    assert resp.json()["camera"]["rtsp_url"] == "rtsp://192.168.1.1/stream"


def test_update_rtsp_not_found(client):
    resp = client.put("/api/v1/cameras/nonexistent", json={"rtsp_url": "rtsp://x"})
    assert resp.status_code == 404


def test_snapshot_json(cam_client):
    resp = cam_client.post("/api/v1/cameras/cam1/snapshot")
    assert resp.status_code == 200
    data = resp.json()
    assert "tracks" in data
    assert data["camera_id"] == "cam1"


def test_snapshot_jpeg(cam_client):
    resp = cam_client.get("/api/v1/cameras/cam1/snapshot.jpg")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.content[:2] == b"\xff\xd8"


def test_stream_lifecycle(cam_client):
    start = cam_client.post("/api/v1/cameras/cam1/stream/start")
    assert start.status_code == 200
    assert start.json()["status"] == "running"

    status = cam_client.get("/api/v1/cameras/cam1/stream/status")
    assert status.json()["status"] == "running"

    stop = cam_client.post("/api/v1/cameras/cam1/stream/stop")
    assert stop.status_code == 200

    status2 = cam_client.get("/api/v1/cameras/cam1/stream/status")
    assert status2.json()["status"] == "stopped"


def test_stream_start_not_found(client):
    resp = client.post("/api/v1/cameras/missing/stream/start")
    assert resp.status_code == 404
