import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_state():
    """Reset all in-memory state before every test."""
    from api.mock_state import state
    state.cameras.clear()
    state.roi_configs.clear()
    state.tracks.clear()
    state.counts.clear()
    state.jobs.clear()
    state.streams.clear()
    state.track_id_seq.clear()
    state.events.clear()
    yield


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


@pytest.fixture
def cam_client(client):
    """TestClient with camera 'cam1' pre-registered."""
    client.post("/api/v1/cameras/", params={"camera_id": "cam1"})
    return client
