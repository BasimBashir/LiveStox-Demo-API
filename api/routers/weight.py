"""Weight Estimation API — GBDT mock endpoints (bbox and segmentation)."""
import random
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from api.schemas import (
    WeightEstimationRequest, WeightEstimationResponse,
    BatchWeightEstimationRequest, BatchWeightEstimationResponse,
)
from api import mock_generators as gen

router = APIRouter()

_ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".bmp"}
_ALLOWED_VIDEO = {".mp4", ".avi", ".mov"}


def _check_ext(filename: str, allowed: set) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Invalid file type. Allowed: {', '.join(sorted(allowed))}")


def _image_response(filename: str, detections: list) -> dict:
    stats = gen.generate_weight_statistics(detections)
    avg = stats["avg_weight_predicted"]
    n = stats["total_chickens"]
    return {
        "source": filename,
        "source_type": "image",
        "statistics": stats,
        "per_chicken_detections": detections,
        "unique_tracked_chickens": None,
        "total_observations": None,
        "annotated_output": f"output/annotated_{filename}",
        "message": f"Analysis completed: {n} chickens detected with avg weight {avg}g",
    }


def _video_response(filename: str, detections: list, use_tracking: bool) -> dict:
    for i, d in enumerate(detections):
        if use_tracking:
            d["track_id"] = i + 1
            d["observations"] = random.randint(5, 50)
    stats = gen.generate_weight_statistics(detections)
    avg = stats["avg_weight_predicted"]
    n = stats["total_chickens"]
    total_obs = sum(d.get("observations", 1) for d in detections)
    return {
        "source": filename,
        "source_type": "video",
        "statistics": stats,
        "per_chicken_detections": detections,
        "unique_tracked_chickens": n if use_tracking else None,
        "total_observations": total_obs if use_tracking else None,
        "annotated_output": f"output/annotated_{filename}",
        "message": f"Video analysis completed: {n} unique chickens with avg weight {avg}g",
    }


@router.post("/estimate", response_model=WeightEstimationResponse)
async def estimate_weight(
    request: WeightEstimationRequest,
    device: str = Query("cuda", pattern="^(cuda|cpu)$"),
):
    """Estimate weight from bounding box dimensions."""
    bbox = request.bbox
    area = round((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]), 1)
    ratio = round((bbox[2] - bbox[0]) / max(bbox[3] - bbox[1], 1), 3)
    return WeightEstimationResponse(
        weight_grams=round(random.uniform(900, 1500), 1),
        confidence=round(random.uniform(0.72, 0.96), 3),
        features={"bbox_area": area, "aspect_ratio": ratio},
    )


@router.post("/batch_estimate", response_model=BatchWeightEstimationResponse)
async def batch_estimate_weight(request: BatchWeightEstimationRequest):
    """Estimate weights for a list of tracks."""
    estimates = [
        {
            "track_id": t.track_id,
            "weight_grams": round(random.uniform(900, 1500), 1),
            "confidence": round(random.uniform(0.72, 0.96), 3),
        }
        for t in request.tracks
    ]
    return BatchWeightEstimationResponse(camera_id=request.camera_id, estimates=estimates)


@router.post("/analyze/image")
async def analyze_image(
    file: UploadFile = File(...),
    conf_threshold: float = Query(0.3),
    save_annotated: bool = Query(False),
    device: str = Query("cuda", pattern="^(cuda|cpu)$"),
    camera_id: str = Query(None),
):
    """Bbox-based weight analysis on a single image."""
    _check_ext(file.filename, _ALLOWED_IMAGE)
    await file.read()
    return _image_response(file.filename, gen.generate_weight_detections())


@router.post("/analyze/image/segmentation")
async def analyze_image_segmentation(
    file: UploadFile = File(...),
    model_type: str = Query("yolov8", pattern="^(yolov8|sam2)$"),
    seg_model_path: str = Query("models/best.pt"),
    detector_model_path: str = Query(None),
    weight_model_path: str = Query("models/weight_gbdt_segmentation.pkl"),
    conf_threshold: float = Query(0.3),
    save_annotated: bool = Query(False),
    save_masks: bool = Query(False),
    device: str = Query("cuda", pattern="^(cuda|cpu)$"),
    camera_id: str = Query(None),
):
    """Segmentation-based weight analysis on a single image (MAE 0.2g)."""
    if model_type == "sam2" and not detector_model_path:
        raise HTTPException(
            400, "detector_model_path is required when using model_type='sam2'"
        )
    _check_ext(file.filename, _ALLOWED_IMAGE)
    await file.read()
    return _image_response(file.filename, gen.generate_weight_detections())


@router.post("/analyze/video")
async def analyze_video(
    file: UploadFile = File(...),
    conf_threshold: float = Query(0.3),
    sample_rate: int = Query(10, ge=1),
    save_annotated: bool = Query(False),
    use_tracking: bool = Query(True),
    device: str = Query("cuda", pattern="^(cuda|cpu)$"),
    camera_id: str = Query(None),
):
    """Bbox-based weight analysis on a video file."""
    _check_ext(file.filename, _ALLOWED_VIDEO)
    await file.read()
    return _video_response(file.filename, gen.generate_weight_detections(), use_tracking)


@router.post("/analyze/video/segmentation")
async def analyze_video_segmentation(
    file: UploadFile = File(...),
    model_type: str = Query("yolov8", pattern="^(yolov8|sam2)$"),
    seg_model_path: str = Query("models/best.pt"),
    detector_model_path: str = Query(None),
    weight_model_path: str = Query("models/weight_gbdt_segmentation.pkl"),
    conf_threshold: float = Query(0.3),
    sample_rate: int = Query(10, ge=1),
    save_annotated: bool = Query(False),
    use_tracking: bool = Query(True),
    device: str = Query("cuda", pattern="^(cuda|cpu)$"),
    camera_id: str = Query(None),
):
    """Segmentation-based weight analysis on a video file (MAE 0.2g)."""
    if model_type == "sam2" and not detector_model_path:
        raise HTTPException(
            400, "detector_model_path is required when using model_type='sam2'"
        )
    _check_ext(file.filename, _ALLOWED_VIDEO)
    await file.read()
    return _video_response(file.filename, gen.generate_weight_detections(), use_tracking)


@router.get("/model_info")
async def model_info():
    return {
        "mode": "DEMO",
        "bbox_model": {"path": "models/weight_gbdt.pkl", "features": 28, "mae_grams": 4.8, "loaded": True},
        "segmentation_model": {"path": "models/weight_gbdt_segmentation.pkl", "features": 33, "mae_grams": 0.2, "loaded": True},
        "yolo_model": {"path": "models/best.pt", "classes": ["<weight_grams>_<age_days>"], "loaded": True},
    }


@router.get("/feature_importance")
async def feature_importance():
    bbox_feat = {f"bbox_feature_{i}": round(random.uniform(0.01, 0.15), 4) for i in range(28)}
    seg_feat = {f"seg_feature_{i}": round(random.uniform(0.01, 0.15), 4) for i in range(33)}
    bbox_feat["age_days"] = 0.42
    seg_feat["age_days"] = 0.51
    return {
        "bbox_model": {"features": bbox_feat, "top_feature": "age_days"},
        "segmentation_model": {"features": seg_feat, "top_feature": "age_days"},
    }
