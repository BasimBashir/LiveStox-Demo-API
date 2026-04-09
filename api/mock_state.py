"""
In-memory singleton state for the ArkAI demo API.
All stores reset on server restart — this is intentional for a demo.
"""
import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AppState:
    # {camera_id: {camera_id, rtsp_url, status, added_at, frame_count}}
    cameras: Dict[str, Dict] = field(default_factory=dict)

    # {camera_id: {zones: {name: {type, points, description}}, lines: {name: {points}}}}
    roi_configs: Dict[str, Dict] = field(default_factory=dict)

    # {camera_id: [track_dict, ...]}  — last frame snapshot per camera
    tracks: Dict[str, List[Dict]] = field(default_factory=dict)

    # {camera_id: {zone_counts: {name: int}, line_counts: {name: {in, out}}, total_unique: int}}
    counts: Dict[str, Dict] = field(default_factory=dict)

    # {job_id: {job_id, camera_id, status, progress_percent, frames_processed, frames_total, result}}
    jobs: Dict[str, Dict] = field(default_factory=dict)

    # {stream_id: {stream_id, camera_id, stream_url, started_at, status, frames_processed}}
    streams: Dict[str, Dict] = field(default_factory=dict)

    # {camera_id: int}  — monotonically increasing track ID counter per camera
    track_id_seq: Dict[str, int] = field(default_factory=dict)

    # Global event log, capped at 1000 entries
    events: List[Dict] = field(default_factory=list)

    # Server start time for uptime calculation
    startup_time: float = field(default_factory=time.time)


# Module-level singleton — import `state` directly everywhere
state = AppState()
