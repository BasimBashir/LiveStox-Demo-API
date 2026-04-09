import pytest
from api.mock_state import AppState
from api import mock_generators as gen


@pytest.fixture
def fresh_state():
    return AppState()


def test_generate_tracks_count_in_range(fresh_state):
    for _ in range(10):
        tracks = gen.generate_tracks("cam1", fresh_state)
        assert 8 <= len(tracks) <= 20


def test_generate_tracks_schema(fresh_state):
    tracks = gen.generate_tracks("cam1", fresh_state)
    t = tracks[0]
    assert "track_id" in t
    assert len(t["bbox"]) == 4
    assert len(t["centroid"]) == 2
    assert 0.0 <= t["confidence"] <= 1.0
    assert isinstance(t["class_name"], str)


def test_track_ids_are_sequential(fresh_state):
    t1 = gen.generate_tracks("cam1", fresh_state)
    t2 = gen.generate_tracks("cam1", fresh_state)
    max_t1 = max(t["track_id"] for t in t1)
    min_t2 = min(t["track_id"] for t in t2)
    assert min_t2 > max_t1


def test_generate_weight_detections_count():
    for _ in range(5):
        d = gen.generate_weight_detections()
        assert 8 <= len(d) <= 20


def test_generate_weight_detections_fixed_count():
    d = gen.generate_weight_detections(5)
    assert len(d) == 5


def test_weight_in_range():
    detections = gen.generate_weight_detections(20)
    for d in detections:
        assert 870 <= d["predicted_weight_grams"] <= 1530


def test_generate_weight_statistics_empty():
    s = gen.generate_weight_statistics([])
    assert s["total_chickens"] == 0
    assert s["avg_weight_predicted"] == 0.0


def test_generate_weight_statistics_values():
    dets = gen.generate_weight_detections(10)
    s = gen.generate_weight_statistics(dets)
    assert s["total_chickens"] == 10
    assert s["avg_weight_predicted"] > 0


def test_increment_counts_initialises_defaults(fresh_state):
    counts = gen.increment_counts("cam1", fresh_state)
    assert "zone_counts" in counts
    assert "line_counts" in counts
    assert "total_unique" in counts


def test_increment_counts_grows(fresh_state):
    c1 = gen.increment_counts("cam1", fresh_state)
    total1 = c1["total_unique"]
    gen.increment_counts("cam1", fresh_state)
    gen.increment_counts("cam1", fresh_state)
    c4 = gen.increment_counts("cam1", fresh_state)
    assert c4["total_unique"] >= total1


def test_solid_colour_jpeg_returns_bytes():
    data = gen.solid_colour_jpeg(320, 240)
    assert isinstance(data, bytes)
    assert data[:2] == b"\xff\xd8"


def test_solid_colour_base64_is_string():
    b64 = gen.solid_colour_base64(320, 240)
    import base64
    decoded = base64.b64decode(b64)
    assert decoded[:2] == b"\xff\xd8"
