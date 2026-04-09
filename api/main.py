"""
ArkAI Demo API
Identical endpoints to the real ArkAI API — returns realistic mock data.
No ML models required. State resets on restart.
"""
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.mock_state import state
from api.routers import tracking, counting, weight, processing, cameras, roi

app = FastAPI(
    title="ArkAI Tracking API",
    description=(
        "**[DEMO MODE]** Bot-SORT tracking + ROI counting + GBDT weight estimation "
        "for multi-camera chicken monitoring. Returns realistic mock data — "
        "no ML models are loaded. Safe to call from any FE environment."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tracking.router, prefix="/api/v1/tracking", tags=["Tracking"])
app.include_router(counting.router, prefix="/api/v1/counting", tags=["Counting"])
app.include_router(weight.router, prefix="/api/v1/weight", tags=["Weight Estimation"])
app.include_router(processing.router, prefix="/api/v1", tags=["Processing"])
app.include_router(cameras.router, prefix="/api/v1/cameras", tags=["Camera Management"])
app.include_router(roi.router, prefix="/api/v1/roi", tags=["ROI Management"])


@app.get("/")
async def root():
    return {
        "name": "ArkAI Tracking API",
        "version": "1.0.0",
        "mode": "DEMO — mock data, no ML models loaded",
        "description": "Multi-camera chicken tracking, counting, and weight estimation",
        "swagger_ui": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "cameras": {
                "list": "GET /api/v1/cameras",
                "add": "POST /api/v1/cameras?camera_id=<id>",
                "update_rtsp": "PUT /api/v1/cameras/{camera_id}",
                "snapshot_json": "POST /api/v1/cameras/{camera_id}/snapshot",
                "snapshot_jpeg": "GET /api/v1/cameras/{camera_id}/snapshot.jpg",
                "stream_start": "POST /api/v1/cameras/{camera_id}/stream/start",
                "stream_stop": "POST /api/v1/cameras/{camera_id}/stream/stop",
                "stream_status": "GET /api/v1/cameras/{camera_id}/stream/status",
            },
            "tracking": "/api/v1/tracking",
            "counting": "/api/v1/counting",
            "weight": {
                "bbox_image": "POST /api/v1/weight/analyze/image",
                "seg_image": "POST /api/v1/weight/analyze/image/segmentation",
                "bbox_video": "POST /api/v1/weight/analyze/video",
                "seg_video": "POST /api/v1/weight/analyze/video/segmentation",
            },
            "roi": "/api/v1/roi",
            "processing": {
                "images": "POST /api/v1/process/images",
                "videos": "POST /api/v1/process/videos",
                "job_status": "GET /api/v1/jobs/{job_id}",
                "stream_start": "POST /api/v1/stream/start",
            },
            "health": "/health",
            "stats": "/stats",
        },
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - state.startup_time, 2),
        "model_loaded": True,
    }


@app.get("/stats")
async def get_system_stats():
    total_tracks = sum(len(t) for t in state.tracks.values())
    total_unique = sum(c.get("total_unique", 0) for c in state.counts.values())
    event_type_counts: dict = {}
    for e in state.events:
        et = e.get("event_type", "unknown")
        event_type_counts[et] = event_type_counts.get(et, 0) + 1

    return {
        "uptime_seconds": round(time.time() - state.startup_time, 2),
        "tracking": {
            "total_cameras": len(state.cameras),
            "total_tracks": total_tracks,
            "active_tracks": total_tracks,
        },
        "counting": {
            "total_cameras": len(state.cameras),
            "total_unique_objects": total_unique,
            "total_events": len(state.events),
        },
        "events": {
            "total_events": len(state.events),
            "event_types": event_type_counts,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
