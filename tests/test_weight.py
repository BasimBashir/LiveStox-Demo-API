import io


def _fake_image():
    return ("image.jpg", io.BytesIO(b"fake"), "image/jpeg")


def _fake_video():
    return ("video.mp4", io.BytesIO(b"fake"), "video/mp4")


def test_estimate_single_weight(client):
    resp = client.post(
        "/api/v1/weight/estimate",
        json={"bbox": [100.0, 200.0, 250.0, 350.0], "class_id": 0, "camera_id": "cam1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert 870 <= data["weight_grams"] <= 1530
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["features"], dict)


def test_analyze_image_bbox(client):
    resp = client.post("/api/v1/weight/analyze/image", files={"file": _fake_image()})
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_type"] == "image"
    assert data["statistics"]["total_chickens"] >= 8
    assert len(data["per_chicken_detections"]) == data["statistics"]["total_chickens"]


def test_analyze_image_invalid_file(client):
    resp = client.post(
        "/api/v1/weight/analyze/image",
        files={"file": ("bad.txt", io.BytesIO(b"x"), "text/plain")},
    )
    assert resp.status_code == 400


def test_analyze_image_segmentation(client):
    resp = client.post(
        "/api/v1/weight/analyze/image/segmentation",
        files={"file": _fake_image()},
        params={"model_type": "yolov8"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_type"] == "image"
    assert data["statistics"]["total_chickens"] >= 8


def test_analyze_image_segmentation_sam2_without_detector(client):
    resp = client.post(
        "/api/v1/weight/analyze/image/segmentation",
        files={"file": _fake_image()},
        params={"model_type": "sam2"},
    )
    assert resp.status_code == 400
    assert "detector_model_path" in resp.json()["detail"]


def test_analyze_video_bbox(client):
    resp = client.post("/api/v1/weight/analyze/video", files={"file": _fake_video()})
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_type"] == "video"
    assert data["unique_tracked_chickens"] is not None


def test_analyze_video_invalid_file(client):
    resp = client.post(
        "/api/v1/weight/analyze/video",
        files={"file": ("bad.jpg", io.BytesIO(b"x"), "image/jpeg")},
    )
    assert resp.status_code == 400


def test_analyze_video_segmentation(client):
    resp = client.post(
        "/api/v1/weight/analyze/video/segmentation",
        files={"file": _fake_video()},
        params={"model_type": "yolov8"},
    )
    assert resp.status_code == 200


def test_model_info(client):
    resp = client.get("/api/v1/weight/model_info")
    assert resp.status_code == 200
    data = resp.json()
    assert "bbox_model" in data
    assert "segmentation_model" in data
    assert data["mode"] == "DEMO"


def test_feature_importance(client):
    resp = client.get("/api/v1/weight/feature_importance")
    assert resp.status_code == 200
    data = resp.json()
    assert "bbox_model" in data
    assert "segmentation_model" in data
