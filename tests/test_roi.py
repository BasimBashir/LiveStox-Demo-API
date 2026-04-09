import io


def _fake_image():
    return ("sample.jpg", io.BytesIO(b"fake"), "image/jpeg")


def test_upload_sample_image(client):
    resp = client.post("/api/v1/roi/sample_image", files={"file": _fake_image()})
    assert resp.status_code == 200
    data = resp.json()
    assert data["standard_width"] == 1280
    assert data["standard_height"] == 720
    assert isinstance(data["image_base64"], str)
    assert len(data["image_base64"]) > 100


def test_upload_sample_image_invalid(client):
    resp = client.post(
        "/api/v1/roi/sample_image",
        files={"file": ("bad.pdf", io.BytesIO(b"x"), "application/pdf")},
    )
    assert resp.status_code == 400


def test_list_all_rois_empty(client):
    resp = client.get("/api/v1/roi/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_camera_rois_empty(client):
    resp = client.get("/api/v1/roi/cam1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["camera_id"] == "cam1"
    assert data["zones"] == []
    assert data["lines"] == []


def test_create_zone(client):
    resp = client.post(
        "/api/v1/roi/cam1/zone",
        json={"zone_name": "feeding_area", "points": [[10, 10], [100, 10], [100, 100], [10, 100]]},
    )
    assert resp.status_code == 200
    assert resp.json()["zone_name"] == "feeding_area"


def test_create_zone_persists(client):
    client.post(
        "/api/v1/roi/cam1/zone",
        json={"zone_name": "zone_a", "points": [[0, 0], [50, 0], [50, 50], [0, 50]]},
    )
    resp = client.get("/api/v1/roi/cam1")
    zones = resp.json()["zones"]
    assert any(z["zone_name"] == "zone_a" for z in zones)


def test_delete_zone(client):
    client.post(
        "/api/v1/roi/cam1/zone",
        json={"zone_name": "zone_x", "points": [[0, 0], [10, 0], [10, 10], [0, 10]]},
    )
    resp = client.delete("/api/v1/roi/cam1/zone/zone_x")
    assert resp.status_code == 200


def test_delete_zone_not_found(client):
    resp = client.delete("/api/v1/roi/cam1/zone/nonexistent")
    assert resp.status_code == 404


def test_create_line(client):
    resp = client.post(
        "/api/v1/roi/cam1/line",
        json={"line_name": "entry_line", "points": [[0, 360], [1280, 360]]},
    )
    assert resp.status_code == 200
    assert resp.json()["line_name"] == "entry_line"


def test_delete_line(client):
    client.post(
        "/api/v1/roi/cam1/line",
        json={"line_name": "line_x", "points": [[0, 0], [100, 100]]},
    )
    resp = client.delete("/api/v1/roi/cam1/line/line_x")
    assert resp.status_code == 200


def test_delete_camera_rois(client):
    client.post(
        "/api/v1/roi/cam1/zone",
        json={"zone_name": "z", "points": [[0, 0], [1, 0], [1, 1], [0, 1]]},
    )
    resp = client.delete("/api/v1/roi/cam1")
    assert resp.status_code == 200


def test_delete_camera_rois_not_found(client):
    resp = client.delete("/api/v1/roi/nonexistent")
    assert resp.status_code == 404


def test_preview_rois(client):
    resp = client.post("/api/v1/roi/cam1/preview", files={"file": _fake_image()})
    assert resp.status_code == 200
    data = resp.json()
    assert "annotated_image_base64" in data
    assert data["camera_id"] == "cam1"
