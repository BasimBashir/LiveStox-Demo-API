"""
Randomized mock data generators for the ArkAI demo API.
All functions are pure (no side effects) except generate_tracks,
which increments track_id_seq in the provided state.
"""
import base64
import io
import random
import time
import uuid
from typing import List, Optional

from api.mock_state import AppState


# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------

def generate_tracks(camera_id: str, state: AppState) -> List[dict]:
    """Generate 8-20 random chicken tracks, incrementing per-camera track IDs."""
    n = random.randint(8, 20)
    tracks = []
    for _ in range(n):
        state.track_id_seq[camera_id] = state.track_id_seq.get(camera_id, 0) + 1
        tid = state.track_id_seq[camera_id]

        x1 = random.randint(0, 1100)
        y1 = random.randint(0, 620)
        x2 = x1 + random.randint(80, 180)
        y2 = y1 + random.randint(80, 100)
        age = random.randint(21, 35)
        w = round(random.uniform(900, 1500), 1)

        tracks.append({
            "track_id": tid,
            "bbox": [float(x1), float(y1), float(x2), float(y2)],
            "class_id": 0,
            "class_name": f"{int(w)}_{age}",
            "confidence": round(random.uniform(0.72, 0.96), 3),
            "centroid": [float((x1 + x2) / 2), float((y1 + y2) / 2)],
        })
    return tracks


# ---------------------------------------------------------------------------
# Weight estimation
# ---------------------------------------------------------------------------

def generate_weight_detections(n_chickens: Optional[int] = None) -> List[dict]:
    """Generate per-chicken weight detections. n_chickens defaults to random 8-20."""
    if n_chickens is None:
        n_chickens = random.randint(8, 20)

    detections = []
    for i in range(n_chickens):
        age = random.randint(21, 35)
        gbdt = round(random.uniform(900, 1500), 1)
        yolo = round(gbdt + random.uniform(-30, 30), 1)
        combined = round((gbdt + yolo) / 2, 1)
        x1 = random.randint(0, 1100)
        y1 = random.randint(0, 620)
        x2 = x1 + random.randint(80, 180)
        y2 = y1 + random.randint(80, 100)

        detections.append({
            "chicken_id": i + 1,
            "track_id": None,
            "observations": 1,
            "age_days": float(age),
            "yolo_weight_grams": yolo,
            "predicted_weight_grams": gbdt,
            "combined_weight_grams": combined,
            "confidence": round(random.uniform(0.72, 0.96), 3),
            "class_name": f"{int(yolo)}_{age}",
            "bbox": [float(x1), float(y1), float(x2), float(y2)],
        })
    return detections


def generate_weight_statistics(detections: List[dict]) -> dict:
    """Aggregate weight statistics from a list of detections."""
    n = len(detections)
    if n == 0:
        return {
            "total_chickens": 0,
            "total_weight_yolo": 0.0,
            "total_weight_predicted": 0.0,
            "total_weight_combined": 0.0,
            "avg_weight_yolo": 0.0,
            "avg_weight_predicted": 0.0,
            "avg_weight_combined": 0.0,
        }

    ty = sum(d["yolo_weight_grams"] for d in detections)
    tp = sum(d["predicted_weight_grams"] for d in detections)
    tc = sum(d["combined_weight_grams"] for d in detections)
    return {
        "total_chickens": n,
        "total_weight_yolo": round(ty, 1),
        "total_weight_predicted": round(tp, 1),
        "total_weight_combined": round(tc, 1),
        "avg_weight_yolo": round(ty / n, 1),
        "avg_weight_predicted": round(tp / n, 1),
        "avg_weight_combined": round(tc / n, 1),
    }


# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------

def increment_counts(camera_id: str, state: AppState) -> dict:
    """
    Return counts for camera_id, slightly incrementing each call.
    Initialises from roi_configs if present, else uses two default zones/lines.
    """
    if camera_id not in state.counts:
        zones: dict = {}
        lines: dict = {}
        cfg = state.roi_configs.get(camera_id, {})
        for name in cfg.get("zones", {}):
            zones[name] = 0
        for name in cfg.get("lines", {}):
            lines[name] = {"in": 0, "out": 0}
        if not zones:
            zones = {"zone_a": 0, "zone_b": 0}
        if not lines:
            lines = {"entry_line": {"in": 0, "out": 0}}

        state.counts[camera_id] = {
            "zone_counts": zones,
            "line_counts": lines,
            "total_unique": 0,
        }

    counts = state.counts[camera_id]
    for z in counts["zone_counts"]:
        counts["zone_counts"][z] += random.randint(0, 3)
    for ln in counts["line_counts"]:
        counts["line_counts"][ln]["in"] += random.randint(0, 2)
        counts["line_counts"][ln]["out"] += random.randint(0, 2)
    counts["total_unique"] += random.randint(0, 5)
    return counts


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def make_event(camera_id: str, track_id: int, roi_name: Optional[str] = None) -> dict:
    """Generate a single counting event dict."""
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": random.choice(["zone_entry", "zone_exit", "line_crossing", "dwelling"]),
        "camera_id": camera_id,
        "track_id": track_id,
        "timestamp": time.time(),
        "roi_name": roi_name,
        "line_name": None,
        "direction": random.choice(["in", "out"]),
        "class_name": f"{random.randint(900, 1500)}_{random.randint(21, 35)}",
    }


# ---------------------------------------------------------------------------
# Image helpers (Pillow — no OpenCV)
# ---------------------------------------------------------------------------

def solid_colour_jpeg(width: int = 320, height: int = 240) -> bytes:
    """Return raw JPEG bytes of a solid random-colour image."""
    from PIL import Image
    r, g, b = random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)
    img = Image.new("RGB", (width, height), (r, g, b))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def solid_colour_base64(width: int = 1280, height: int = 720) -> str:
    """Return base64-encoded solid-colour JPEG string."""
    return base64.b64encode(solid_colour_jpeg(width, height)).decode()
