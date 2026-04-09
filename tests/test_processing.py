import time


def test_process_images_returns_job_id(client):
    resp = client.post(
        "/api/v1/process/images",
        params={"directory_path": "/data/images", "camera_id": "cam1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "processing"


def test_process_videos_returns_job_id(client):
    resp = client.post(
        "/api/v1/process/videos",
        params={"directory_path": "/data/videos", "camera_id": "cam1"},
    )
    assert resp.status_code == 200
    assert "job_id" in resp.json()


def test_job_status_processing(client):
    create = client.post(
        "/api/v1/process/images",
        params={"directory_path": "/data", "camera_id": "cam1"},
    )
    job_id = create.json()["job_id"]
    resp = client.get(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("processing", "completed")
    assert data["job_id"] == job_id


def test_job_not_found(client):
    resp = client.get("/api/v1/jobs/nonexistent-id")
    assert resp.status_code == 404


def test_job_completes(client):
    """Job should complete within 5 seconds."""
    create = client.post(
        "/api/v1/process/images",
        params={"directory_path": "/data", "camera_id": "cam1"},
    )
    job_id = create.json()["job_id"]
    deadline = time.time() + 5
    while time.time() < deadline:
        resp = client.get(f"/api/v1/jobs/{job_id}")
        if resp.json()["status"] == "completed":
            assert resp.json()["result"] is not None
            return
        time.sleep(0.5)
    raise AssertionError("Job did not complete within 5 seconds")


def test_stream_start(client):
    resp = client.post(
        "/api/v1/stream/start",
        params={"stream_url": "rtsp://192.168.1.1/stream", "camera_id": "cam1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "stream_id" in data
    assert data["status"] == "running"


def test_stream_stop(client):
    start = client.post(
        "/api/v1/stream/start",
        params={"stream_url": "rtsp://x/s", "camera_id": "cam1"},
    )
    sid = start.json()["stream_id"]
    resp = client.post("/api/v1/stream/stop", params={"stream_id": sid})
    assert resp.status_code == 200


def test_stream_status(client):
    start = client.post(
        "/api/v1/stream/start",
        params={"stream_url": "rtsp://x/s", "camera_id": "cam1"},
    )
    sid = start.json()["stream_id"]
    resp = client.get("/api/v1/stream/status", params={"stream_id": sid})
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_stream_results(client):
    start = client.post(
        "/api/v1/stream/start",
        params={"stream_url": "rtsp://x/s", "camera_id": "cam1"},
    )
    sid = start.json()["stream_id"]
    resp = client.get("/api/v1/stream/results", params={"stream_id": sid})
    assert resp.status_code == 200
    data = resp.json()
    assert "detections" in data
    assert "statistics" in data
