"""Processing API — batch image/video jobs and live stream management."""
import asyncio
import random
import time
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from api.mock_state import state
from api import mock_generators as gen

router = APIRouter()


async def _complete_job(job_id: str) -> None:
    """Auto-complete a job after 3 seconds to simulate processing time."""
    await asyncio.sleep(3)
    if job_id not in state.jobs:
        return
    detections = gen.generate_weight_detections()
    stats = gen.generate_weight_statistics(detections)
    frames = state.jobs[job_id].get("frames_total", 100)
    state.jobs[job_id].update({
        "status": "completed",
        "progress_percent": 100.0,
        "frames_processed": frames,
        "result": {
            "summary": {
                "total_detections": len(detections) * frames,
                "unique_count": len(detections),
                "average_weight": stats["avg_weight_predicted"],
                "total_weight": stats["total_weight_predicted"],
                "min_weight": min(d["predicted_weight_grams"] for d in detections),
                "max_weight": max(d["predicted_weight_grams"] for d in detections),
                "zone_counts": {},
                "line_counts": {},
                "processing_time": 3.0,
                "frames_processed": frames,
            },
            "detections": detections,
        },
    })


def _create_job(camera_id: str, frames_total: int, bg: BackgroundTasks) -> str:
    job_id = str(uuid.uuid4())
    state.jobs[job_id] = {
        "job_id": job_id,
        "camera_id": camera_id,
        "status": "processing",
        "progress_percent": 0.0,
        "frames_processed": 0,
        "frames_total": frames_total,
        "created_at": time.time(),
        "result": None,
    }
    bg.add_task(_complete_job, job_id)
    return job_id


@router.post("/process/images")
async def process_image_directory(
    background_tasks: BackgroundTasks,
    directory_path: str = Query(..., description="Local path to image directory"),
    camera_id: str = Query(..., description="Camera identifier"),
    recursive: bool = Query(False),
    enable_counting: bool = Query(True),
    enable_weight: bool = Query(True),
    device: str = Query("cuda", pattern="^(cuda|cpu)$"),
):
    """Start batch processing of an image directory. Returns job_id immediately."""
    job_id = _create_job(camera_id, random.randint(50, 200), background_tasks)
    return {"job_id": job_id, "status": "processing", "directory_path": directory_path, "camera_id": camera_id}


@router.post("/process/videos")
async def process_video_directory(
    background_tasks: BackgroundTasks,
    directory_path: str = Query(..., description="Local path to video directory"),
    camera_id: str = Query(..., description="Camera identifier"),
    recursive: bool = Query(False),
    enable_counting: bool = Query(True),
    enable_weight: bool = Query(True),
    device: str = Query("cuda", pattern="^(cuda|cpu)$"),
):
    """Start batch processing of a video directory. Returns job_id immediately."""
    job_id = _create_job(camera_id, random.randint(200, 1000), background_tasks)
    return {"job_id": job_id, "status": "processing", "directory_path": directory_path, "camera_id": camera_id}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Poll job status. Status transitions: processing -> completed after ~3s."""
    if job_id not in state.jobs:
        raise HTTPException(404, f"Job '{job_id}' not found")
    j = state.jobs[job_id]
    return {
        "job_id": job_id,
        "status": j["status"],
        "progress_percent": j["progress_percent"],
        "frames_processed": j["frames_processed"],
        "frames_total": j["frames_total"],
        "camera_id": j["camera_id"],
        "result": j.get("result"),
    }


@router.post("/stream/start")
async def stream_start(
    stream_url: str = Query(..., description="RTSP/HTTP stream URL"),
    camera_id: str = Query(...),
    enable_counting: bool = Query(True),
    enable_weight: bool = Query(True),
    frame_skip: int = Query(1, ge=1),
):
    """Start a live stream processing session."""
    stream_id = str(uuid.uuid4())
    state.streams[stream_id] = {
        "stream_id": stream_id,
        "camera_id": camera_id,
        "stream_url": stream_url,
        "started_at": time.time(),
        "status": "running",
        "frames_processed": 0,
    }
    return {"stream_id": stream_id, "camera_id": camera_id, "status": "running"}


@router.post("/stream/stop")
async def stream_stop(stream_id: str = Query(...)):
    """Stop a live stream by stream_id."""
    if stream_id not in state.streams:
        raise HTTPException(404, f"Stream '{stream_id}' not found")
    state.streams[stream_id]["status"] = "stopped"
    return {"stream_id": stream_id, "status": "stopped"}


@router.get("/stream/status")
async def stream_status(stream_id: str = Query(...)):
    """Get status of a stream by stream_id."""
    if stream_id not in state.streams:
        raise HTTPException(404, f"Stream '{stream_id}' not found")
    return state.streams[stream_id]


@router.get("/stream/results")
async def stream_results(stream_id: str = Query(...)):
    """Get accumulated mock results for an active stream."""
    if stream_id not in state.streams:
        raise HTTPException(404, f"Stream '{stream_id}' not found")
    detections = gen.generate_weight_detections()
    stats = gen.generate_weight_statistics(detections)
    s = state.streams[stream_id]
    s["frames_processed"] += random.randint(1, 5)
    return {
        "stream_id": stream_id,
        "camera_id": s["camera_id"],
        "status": s["status"],
        "frames_processed": s["frames_processed"],
        "detections": detections,
        "statistics": stats,
    }
