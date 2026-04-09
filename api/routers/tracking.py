"""Tracking API — Bot-SORT mock endpoints."""
import time
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, Query, HTTPException
from api.schemas import Track, TrackingResponse
from api.mock_state import state
from api import mock_generators as gen

router = APIRouter()

_ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".bmp"}


def _check_image_ext(filename: str) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in _ALLOWED_IMAGE:
        raise HTTPException(
            400, f"Invalid file type. Allowed: {', '.join(sorted(_ALLOWED_IMAGE))}"
        )


@router.post("/track_frame", response_model=TrackingResponse)
async def track_frame(
    camera_id: str = Query(..., description="Camera identifier"),
    file: UploadFile = File(..., description="Image file (JPG, PNG, BMP)"),
    device: str = Query("cuda", pattern="^(cuda|cpu)$"),
):
    """Track objects in a single frame. Returns 8-20 randomised chicken tracks."""
    _check_image_ext(file.filename)
    await file.read()

    tracks = gen.generate_tracks(camera_id, state)
    state.tracks[camera_id] = tracks

    for t in tracks[:2]:
        evt = gen.make_event(camera_id, t["track_id"])
        state.events.append(evt)
    if len(state.events) > 1000:
        state.events = state.events[-1000:]

    return TrackingResponse(
        camera_id=camera_id,
        timestamp=time.time(),
        tracks=[Track(**t) for t in tracks],
        active_track_count=len(tracks),
    )


@router.get("/active_tracks")
async def get_active_tracks(
    camera_id: str = Query(None, description="Camera ID (omit for all cameras)"),
):
    """Return currently active tracks for one camera or all cameras."""
    if camera_id:
        active = state.tracks.get(camera_id, [])
        return {"camera_id": camera_id, "active_tracks": active, "count": len(active)}
    total = sum(len(t) for t in state.tracks.values())
    return {"all_cameras": dict(state.tracks), "total_count": total}


@router.get("/track_info/{track_id}")
async def get_track_info(
    track_id: int,
    camera_id: str = Query(..., description="Camera ID"),
):
    """Get details for a specific track. Returns 404 if not found."""
    for t in state.tracks.get(camera_id, []):
        if t["track_id"] == track_id:
            return {**t, "history_length": 1, "first_seen": time.time() - 5.0}
    raise HTTPException(404, f"Track {track_id} not found on camera {camera_id}")


@router.get("/statistics")
async def get_tracking_statistics():
    """Tracking statistics across all cameras."""
    return {
        "total_cameras": len(state.tracks),
        "total_tracks_created": dict(state.track_id_seq),
        "active_tracks": {cam: len(t) for cam, t in state.tracks.items()},
    }


@router.post("/reset/{camera_id}")
async def reset_tracking(camera_id: str):
    """Clear all track history and reset track ID counter for a camera."""
    state.tracks.pop(camera_id, None)
    state.track_id_seq.pop(camera_id, None)
    return {"message": f"Tracking reset for camera {camera_id}"}
