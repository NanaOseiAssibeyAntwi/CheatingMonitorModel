from __future__ import annotations

from pydantic import BaseModel, Field


class LandmarkPoint(BaseModel):
    id: int
    x: float
    y: float
    z: float = 0.0
    pixel_x: int = 0
    pixel_y: int = 0


class FeaturePayload(BaseModel):
    gaze_x: float
    gaze_y: float
    blink_rate: float
    head_yaw: float
    head_pitch: float
    head_roll: float
    ear: float | None = None
    mouth_mar: float | None = None
    mouth_movement: float | None = None
    speech_activity: float | None = None
    is_speaking: bool | None = None


class AnalysisRequestBase(BaseModel):
    session_id: str | None = Field(
        default=None,
        description="Optional in-memory session for temporal blink-rate and rolling-score state.",
    )
    classifier_output: int | None = Field(default=None, ge=0, le=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class AnalyzeLandmarksRequest(AnalysisRequestBase):
    face_count: int = Field(default=1, ge=0)
    landmarks: list[LandmarkPoint] = Field(min_length=1)


class ScoreRequest(AnalysisRequestBase):
    face_count: int = Field(default=1, ge=0)
    features: FeaturePayload


class SessionResponse(BaseModel):
    session_id: str


class DatasetFileItem(BaseModel):
    name: str
    size_bytes: int
    modified_at: str


class AnalysisResponse(BaseModel):
    detected: bool
    face_count: int
    session_id: str | None = None
    features: FeaturePayload | None = None
    score: int | None = None
    label: str
    label_color: list[int]
    observations: list[str] = Field(default_factory=list)
    signals: list[DetectionSignal] = Field(default_factory=list)


class ScoreResponse(BaseModel):
    session_id: str | None = None
    face_count: int
    score: int
    label: str
    label_color: list[int]
    features: FeaturePayload
    observations: list[str] = Field(default_factory=list)
    signals: list[DetectionSignal] = Field(default_factory=list)


class DetectionSignal(BaseModel):
    code: str
    category: str
    severity: str
    value: float | None = None
    threshold: float | None = None
    message: str


class VideoFrameResult(BaseModel):
    frame_index: int
    timestamp_seconds: float
    sample_window_seconds: float | None = None
    timestamp_source: str | None = None
    detected: bool
    face_count: int
    score: int | None = None
    label: str
    label_color: list[int]
    observations: list[str]
    signals: list[DetectionSignal] = Field(default_factory=list)
    features: FeaturePayload | None = None
    landmarks: list[LandmarkPoint] | None = None


class VideoEvent(BaseModel):
    start_timestamp_seconds: float
    end_timestamp_seconds: float
    duration_seconds: float
    start_frame_index: int
    end_frame_index: int
    label: str
    severity: str | None = None
    reason: str
    signal_code: str | None = None
    max_score: int | None = None
    frame_count: int


class VideoAlert(BaseModel):
    start_timestamp_seconds: float
    end_timestamp_seconds: float
    duration_seconds: float
    label: str
    severity: str
    reason: str
    signal_code: str | None = None


class VideoAnalysisResponse(BaseModel):
    session_id: str | None = None
    filename: str
    frames_processed: int
    frames_sampled: int
    fps: float
    timestamp_source: str
    duration_seconds: float
    detections: int
    max_score: int
    average_score: float
    final_label: str
    suspicious_event_count: int
    events: list[VideoEvent]
    alerts: list[VideoAlert]
    frame_results: list[VideoFrameResult]


class VideoSummaryKeyFrame(BaseModel):
    frame_index: int
    timestamp_seconds: float
    label: str
    score: int | None = None
    observations: list[str]
    signals: list[DetectionSignal] = Field(default_factory=list)


class VideoSummaryResponse(BaseModel):
    session_id: str | None = None
    filename: str
    frames_processed: int
    frames_sampled: int
    fps: float
    timestamp_source: str
    duration_seconds: float
    detections: int
    max_score: int
    average_score: float
    final_label: str
    suspicious_event_count: int
    events: list[VideoEvent]
    alerts: list[VideoAlert]
    key_frames: list[VideoSummaryKeyFrame]
