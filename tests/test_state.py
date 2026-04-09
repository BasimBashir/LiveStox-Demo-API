from api.mock_state import state


def test_state_starts_empty():
    assert state.cameras == {}
    assert state.roi_configs == {}
    assert state.tracks == {}
    assert state.counts == {}
    assert state.jobs == {}
    assert state.streams == {}
    assert state.track_id_seq == {}
    assert state.events == []


def test_state_is_singleton():
    from api.mock_state import state as s2
    state.cameras["x"] = {}
    assert s2.cameras["x"] == {}
    state.cameras.clear()
