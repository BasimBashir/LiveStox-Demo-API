"""Counting API — ROI zone and line-crossing mock endpoints."""
import random

from fastapi import APIRouter, Query
from api.schemas import CountingResponse, ROICount, LineCount
from api.mock_state import state
from api import mock_generators as gen

router = APIRouter()


@router.get("/counts", response_model=CountingResponse)
async def get_counts(camera_id: str = Query(..., description="Camera identifier")):
    """Get current counts for camera ROIs. Counts increment slightly on each call."""
    counts = gen.increment_counts(camera_id, state)
    zone_counts = [
        ROICount(roi_name=k, count=v) for k, v in counts["zone_counts"].items()
    ]
    line_counts = [
        LineCount(line_name=k, count_in=v["in"], count_out=v["out"])
        for k, v in counts["line_counts"].items()
    ]
    return CountingResponse(
        camera_id=camera_id,
        zone_counts=zone_counts,
        line_counts=line_counts,
        total_unique_objects=counts["total_unique"],
    )


@router.get("/all_counts")
async def get_all_counts():
    """Get counts for all registered cameras."""
    all_counts = {cam: gen.increment_counts(cam, state) for cam in state.cameras}
    return {"cameras": all_counts, "total_cameras": len(all_counts)}


@router.get("/events")
async def get_counting_events(
    camera_id: str = Query(None, description="Filter by camera ID"),
    event_type: str = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get counting event history with optional filters."""
    events = list(state.events)
    if camera_id:
        events = [e for e in events if e["camera_id"] == camera_id]
    if event_type:
        events = [e for e in events if e["event_type"] == event_type]
    page = events[-limit:]
    return {"events": page, "count": len(page)}


@router.get("/roi_density/{camera_id}/{roi_name}")
async def get_roi_density(camera_id: str, roi_name: str):
    """Get current and 30-frame average density for an ROI zone."""
    counts = state.counts.get(camera_id, {})
    current = counts.get("zone_counts", {}).get(roi_name, random.randint(0, 15))
    average = round(random.uniform(5.0, 15.0), 2)
    return {
        "camera_id": camera_id,
        "roi_name": roi_name,
        "current_count": current,
        "average_density_30frames": average,
    }


@router.post("/reset_counts")
async def reset_counts(
    camera_id: str = Query(None, description="Camera to reset; omit to reset all"),
):
    """Reset counts for one camera or all cameras."""
    if camera_id:
        state.counts.pop(camera_id, None)
    else:
        state.counts.clear()
    target = camera_id or "all cameras"
    return {"message": f"Counts reset for {target}"}


@router.get("/statistics")
async def get_counting_statistics(
    camera_id: str = Query(None, description="Camera filter"),
):
    """Return raw counts dict for one camera or all."""
    if camera_id:
        return state.counts.get(camera_id, {})
    return dict(state.counts)
