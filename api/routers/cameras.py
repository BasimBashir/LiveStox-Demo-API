"""Camera Management API — register cameras, snapshots, streaming."""
import time
import uuid

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from api.mock_state import state
from api import mock_generators as gen

router = APIRouter()


class RTSPUpdate(BaseModel):
    rtsp_url: str


@router.get("/")
async def list_cameras():
    """List all registered cameras."""
    return {"cameras": list(state.cameras.values()), "total": len(state.cameras)}


@router.post("/")
async def add_camera(camera_id: str = Query(..., description="Unique camera identifier")):
    """Register a new camera."""
    if camera_id in state.cameras:
        raise HTTPException(400, f"Camera '{camera_id}' already exists")
    state.cameras[camera_id] = {
        "camera_id": camera_id,
        "rtsp_url": None,
        "status": "inactive",
        "added_at": time.time(),
        "frame_count": 0,
    }
    return {"message": f"Camera '{camera_id}' added", "camera": state.cameras[camera_id]}


@router.put("/{camera_id}")
async def update_rtsp(camera_id: str, body: RTSPUpdate):
    """Update RTSP stream URL for a camera."""
    if camera_id not in state.cameras:
        raise HTTPException(404, f"Camera '{camera_id}' not found")
    state.cameras[camera_id]["rtsp_url"] = body.rtsp_url
    return {"message": f"RTSP URL updated for camera '{camera_id}'", "camera": state.cameras[camera_id]}


@router.post("/{camera_id}/snapshot")
async def snapshot_json(camera_id: str):
    """Take a JSON snapshot: returns mock tracks for the camera frame."""
    if camera_id not in state.cameras:
        raise HTTPException(404, f"Camera '{camera_id}' not found")
    tracks = gen.generate_tracks(camera_id, state)
    state.tracks[camera_id] = tracks
    state.cameras[camera_id]["frame_count"] += 1
    return {
        "camera_id": camera_id,
        "timestamp": time.time(),
        "frame_count": state.cameras[camera_id]["frame_count"],
        "tracks": tracks,
        "active_track_count": len(tracks),
    }


@router.get("/{camera_id}/snapshot.jpg")
async def snapshot_jpeg(camera_id: str):
    """Return a JPEG snapshot image (solid colour in demo)."""
    if camera_id not in state.cameras:
        raise HTTPException(404, f"Camera '{camera_id}' not found")
    return Response(content=gen.solid_colour_jpeg(320, 240), media_type="image/jpeg")


@router.post("/{camera_id}/stream/start")
async def stream_start(camera_id: str):
    """Start streaming for a camera. Returns a stream_id."""
    if camera_id not in state.cameras:
        raise HTTPException(404, f"Camera '{camera_id}' not found")
    stream_id = str(uuid.uuid4())
    state.streams[stream_id] = {
        "stream_id": stream_id,
        "camera_id": camera_id,
        "started_at": time.time(),
        "status": "running",
        "frames_processed": 0,
    }
    state.cameras[camera_id]["status"] = "streaming"
    return {"stream_id": stream_id, "camera_id": camera_id, "status": "running"}


@router.post("/{camera_id}/stream/stop")
async def stream_stop(camera_id: str):
    """Stop all active streams for a camera."""
    if camera_id not in state.cameras:
        raise HTTPException(404, f"Camera '{camera_id}' not found")
    for sid, s in state.streams.items():
        if s["camera_id"] == camera_id and s["status"] == "running":
            state.streams[sid]["status"] = "stopped"
    state.cameras[camera_id]["status"] = "inactive"
    return {"message": f"Stream stopped for camera '{camera_id}'"}


@router.get("/{camera_id}/stream/status")
async def stream_status(camera_id: str):
    """Get stream status for a camera."""
    if camera_id not in state.cameras:
        raise HTTPException(404, f"Camera '{camera_id}' not found")
    for s in state.streams.values():
        if s["camera_id"] == camera_id:
            return s
    return {"camera_id": camera_id, "status": "no_active_stream"}
