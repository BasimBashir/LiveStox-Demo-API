"""ROI Management API — define polygon zones and counting lines per camera."""
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel, Field
from api.mock_state import state
from api import mock_generators as gen

router = APIRouter()

_ALLOWED = {".jpg", ".jpeg", ".png", ".bmp"}


class ZoneCreate(BaseModel):
    zone_name: str
    points: List[List[float]] = Field(..., min_length=3)
    description: Optional[str] = None


class LineCreate(BaseModel):
    line_name: str
    points: List[List[float]] = Field(..., min_length=2, max_length=2)


def _check_image(filename: str) -> None:
    if Path(filename).suffix.lower() not in _ALLOWED:
        raise HTTPException(400, f"Invalid file type. Allowed: {', '.join(sorted(_ALLOWED))}")


def _ensure(camera_id: str) -> None:
    if camera_id not in state.roi_configs:
        state.roi_configs[camera_id] = {"zones": {}, "lines": {}}


def _serialise(camera_id: str) -> dict:
    cfg = state.roi_configs.get(camera_id, {"zones": {}, "lines": {}})
    return {
        "camera_id": camera_id,
        "zones": [
            {"zone_name": k, "type": "polygon", "points": v["points"], "description": v.get("description")}
            for k, v in cfg.get("zones", {}).items()
        ],
        "lines": [
            {"line_name": k, "points": v["points"]}
            for k, v in cfg.get("lines", {}).items()
        ],
    }


@router.post("/sample_image")
async def upload_sample_image(file: UploadFile = File(...)):
    """Upload a camera sample image; returns base64 for browser-based ROI drawing."""
    _check_image(file.filename)
    await file.read()
    return {
        "width": 1920,
        "height": 1080,
        "standard_width": 1280,
        "standard_height": 720,
        "image_base64": gen.solid_colour_base64(1280, 720),
    }


@router.get("/")
async def list_all_rois():
    """List ROI configs for all cameras."""
    return [_serialise(cam_id) for cam_id in state.roi_configs]


@router.get("/{camera_id}")
async def get_camera_rois(camera_id: str):
    """Get zones and lines for a specific camera."""
    return _serialise(camera_id)


@router.post("/{camera_id}/zone")
async def create_zone(camera_id: str, body: ZoneCreate):
    """Create or update a polygon zone for a camera (coordinates in 1280x720 space)."""
    _ensure(camera_id)
    state.roi_configs[camera_id]["zones"][body.zone_name] = {
        "type": "polygon",
        "points": body.points,
        "description": body.description,
    }
    return {"message": f"Zone '{body.zone_name}' saved for camera '{camera_id}'",
            "zone_name": body.zone_name, "points": body.points}


@router.delete("/{camera_id}/zone/{zone_name}")
async def delete_zone(camera_id: str, zone_name: str):
    """Delete a polygon zone."""
    cfg = state.roi_configs.get(camera_id, {})
    if zone_name not in cfg.get("zones", {}):
        raise HTTPException(404, f"Zone '{zone_name}' not found for camera '{camera_id}'")
    del state.roi_configs[camera_id]["zones"][zone_name]
    return {"message": f"Zone '{zone_name}' deleted from camera '{camera_id}'"}


@router.post("/{camera_id}/line")
async def create_line(camera_id: str, body: LineCreate):
    """Create or update a counting line for a camera (exactly 2 points)."""
    _ensure(camera_id)
    state.roi_configs[camera_id]["lines"][body.line_name] = {"points": body.points}
    return {"message": f"Line '{body.line_name}' saved for camera '{camera_id}'",
            "line_name": body.line_name, "points": body.points}


@router.delete("/{camera_id}/line/{line_name}")
async def delete_line(camera_id: str, line_name: str):
    """Delete a counting line."""
    cfg = state.roi_configs.get(camera_id, {})
    if line_name not in cfg.get("lines", {}):
        raise HTTPException(404, f"Line '{line_name}' not found for camera '{camera_id}'")
    del state.roi_configs[camera_id]["lines"][line_name]
    return {"message": f"Line '{line_name}' deleted from camera '{camera_id}'"}


@router.delete("/{camera_id}")
async def delete_camera_rois(camera_id: str):
    """Delete all zones and lines for a camera."""
    if camera_id not in state.roi_configs:
        raise HTTPException(404, f"No ROI configuration found for camera '{camera_id}'")
    del state.roi_configs[camera_id]
    return {"message": f"All ROIs deleted for camera '{camera_id}'"}


@router.post("/{camera_id}/preview")
async def preview_rois(camera_id: str, file: UploadFile = File(...)):
    """Upload image and get back an annotated version showing current ROIs."""
    _check_image(file.filename)
    await file.read()
    cfg = state.roi_configs.get(camera_id, {"zones": {}, "lines": {}})
    return {
        "camera_id": camera_id,
        "zones_count": len(cfg.get("zones", {})),
        "lines_count": len(cfg.get("lines", {})),
        "zones": list(cfg.get("zones", {}).keys()),
        "lines": list(cfg.get("lines", {}).keys()),
        "annotated_image_base64": gen.solid_colour_base64(1280, 720),
    }
