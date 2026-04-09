"""
Pydantic Schemas for API Request/Response Models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


# Detection Schemas
class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    class_id: int = Field(..., description="Class ID")
    class_name: str = Field(..., description="Class name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")


class DetectionResponse(BaseModel):
    camera_id: str
    timestamp: float
    detections: List[Detection]
    count: int


# Tracking Schemas
class Track(BaseModel):
    track_id: int = Field(..., description="Unique track ID")
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    class_id: int
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    centroid: List[float] = Field(..., description="Centroid [x, y]")


class TrackingResponse(BaseModel):
    camera_id: str
    timestamp: float
    tracks: List[Track]
    active_track_count: int


# Counting Schemas
class ROICount(BaseModel):
    roi_name: str
    count: int


class LineCount(BaseModel):
    line_name: str
    count_in: int
    count_out: int


class CountingResponse(BaseModel):
    camera_id: str
    zone_counts: List[ROICount]
    line_counts: List[LineCount]
    total_unique_objects: int


# Weight Estimation Schemas
class WeightEstimationRequest(BaseModel):
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    class_id: int
    camera_id: str = "camera_1"
    detection_confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class WeightEstimationResponse(BaseModel):
    weight_grams: float = Field(..., description="Estimated weight in grams")
    confidence: float = Field(..., description="Prediction confidence")
    features: Dict = Field(..., description="Morphometric features used")


class BatchWeightEstimationRequest(BaseModel):
    tracks: List[Track]
    camera_id: str = "camera_1"


class BatchWeightEstimationResponse(BaseModel):
    camera_id: str
    estimates: List[Dict]  # List of {track_id, weight_grams, confidence}


# Statistics Schemas
class CameraStats(BaseModel):
    camera_id: str
    is_active: bool
    frame_count: int
    fps: float
    total_tracks: int
    active_tracks: int


class SystemStats(BaseModel):
    total_cameras: int
    active_cameras: int
    total_detections: int
    total_tracks: int
    uptime_seconds: float
    camera_stats: List[CameraStats]


# Event Schemas
class Event(BaseModel):
    event_id: Optional[str] = None
    event_type: str  # zone_entry, zone_exit, line_crossing, dwelling
    camera_id: str
    track_id: int
    timestamp: float
    roi_name: Optional[str] = None
    line_name: Optional[str] = None
    direction: Optional[str] = None
    class_name: Optional[str] = None


class EventsResponse(BaseModel):
    events: List[Event]
    total_count: int


# Processing Schemas (for batch and stream processing)
class ProcessingRequest(BaseModel):
    directory_path: Optional[str] = None
    stream_url: Optional[str] = None
    camera_id: str
    enable_counting: bool = True
    enable_weight: bool = True
    frame_skip: int = Field(default=1, ge=1, description="Process every Nth frame")


class ProcessingStatus(BaseModel):
    job_id: Optional[str] = None
    stream_id: Optional[str] = None
    status: str  # processing, completed, error, running, stopped
    progress_percent: Optional[float] = None
    frames_processed: Optional[int] = None
    frames_total: Optional[int] = None


class ProcessingResult(BaseModel):
    job_id: Optional[str] = None
    camera_id: str
    results: List[Dict]
    total_count: int


class StreamConfig(BaseModel):
    stream_url: str = Field(..., description="RTSP/HTTP stream URL")
    camera_id: str
    enable_counting: bool = True
    enable_weight: bool = True
    frame_skip: int = Field(default=1, ge=1)
    save_results: bool = True


# Complete Analysis Schemas
class CompleteAnalysisRequest(BaseModel):
    input_type: str = Field(..., description="Input type: 'images', 'videos', or 'stream'")
    source: str = Field(..., description="Directory path (images/videos) or stream URL")
    camera_id: str = Field(default="camera_1")
    enable_counting: bool = True
    enable_weight: bool = True
    frame_skip: int = Field(default=1, ge=1)
    recursive: bool = Field(default=False, description="For directories: process recursively")
    wait_for_completion: bool = Field(default=True, description="Wait and return results or return job_id")
    stream_duration: Optional[int] = Field(default=None, description="For streams: duration in seconds")


class AnalysisSummary(BaseModel):
    total_detections: int = Field(..., description="Total detections across all frames")
    unique_count: int = Field(..., description="Unique tracked objects")
    average_weight: float = Field(..., description="Average weight in grams")
    total_weight: float = Field(..., description="Total weight in grams")
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None
    zone_counts: Dict[str, int] = Field(default_factory=dict)
    line_counts: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    processing_time: float = Field(..., description="Processing time in seconds")
    frames_processed: int = 0


class CompleteAnalysisResponse(BaseModel):
    job_id: str
    status: str
    summary: AnalysisSummary
    detections: List[Dict] = Field(default_factory=list, description="Detailed detections")
    metadata: Dict = Field(default_factory=dict)
