from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from cheating_detector.api.schemas import (
    AnalysisResponse,
    AnalyzeLandmarksRequest,
    DatasetFileItem,
    ScoreRequest,
    ScoreResponse,
    SessionResponse,
    VideoAnalysisResponse,
    VideoSummaryResponse,
)
from cheating_detector.services.analyzer import AnalysisService
from cheating_detector.settings import APP_NAME, APP_VERSION, get_allowed_origins

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "FastAPI wrapper around the cheating detection pipeline. "
        "Use `session_id` when sending multiple frames so temporal metrics "
        "like blink rate and rolling suspicion score remain stable."
    ),
)

allowed_origins = get_allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allowed_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

service = AnalysisService()


@app.get("/")
def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "session_support": True,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/sessions", response_model=SessionResponse)
def create_session():
    return {"session_id": service.create_session()}


@app.delete("/api/v1/sessions/{session_id}")
def delete_session(session_id: str):
    if not service.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"deleted": True, "session_id": session_id}


@app.post("/api/v1/sessions/{session_id}/reset")
def reset_session(session_id: str):
    if not service.reset_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"reset": True, "session_id": session_id}


@app.post("/api/v1/analyze/landmarks", response_model=AnalysisResponse)
def analyze_landmarks(payload: AnalyzeLandmarksRequest):
    try:
        normalized_landmarks = service.normalize_landmarks(payload.landmarks)
        return service.analyze_landmarks(
            landmarks=normalized_landmarks,
            face_count=payload.face_count,
            session_id=payload.session_id,
            classifier_output=payload.classifier_output,
            confidence=payload.confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/analyze/image", response_model=AnalysisResponse)
async def analyze_image(
    image: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    classifier_output: int | None = Form(default=None),
    confidence: float = Form(default=1.0),
):
    try:
        return service.analyze_image_bytes(
            image_bytes=await image.read(),
            session_id=session_id,
            classifier_output=classifier_output,
            confidence=confidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/analyze/video", response_model=VideoAnalysisResponse)
async def analyze_video(
    video: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    classifier_output: int | None = Form(default=None),
    confidence: float = Form(default=1.0),
    sample_every_n_frames: int = Form(default=10),
    max_frames: int = Form(default=30),
    include_landmarks: bool = Form(default=True),
):
    try:
        return service.analyze_video_bytes(
            video_bytes=await video.read(),
            filename=video.filename or "upload.mp4",
            session_id=session_id,
            classifier_output=classifier_output,
            confidence=confidence,
            sample_every_n_frames=sample_every_n_frames,
            max_frames=max_frames,
            include_landmarks=include_landmarks,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/analyze/video/summary", response_model=VideoSummaryResponse)
async def analyze_video_summary(
    video: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    classifier_output: int | None = Form(default=None),
    confidence: float = Form(default=1.0),
    sample_every_n_frames: int = Form(default=10),
    max_frames: int = Form(default=30),
    max_key_frames: int = Form(default=5),
):
    try:
        analysis = service.analyze_video_bytes(
            video_bytes=await video.read(),
            filename=video.filename or "upload.mp4",
            session_id=session_id,
            classifier_output=classifier_output,
            confidence=confidence,
            sample_every_n_frames=sample_every_n_frames,
            max_frames=max_frames,
            include_landmarks=False,
        )
        return service.summarize_video_analysis(
            analysis_result=analysis,
            max_key_frames=max_key_frames,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/score", response_model=ScoreResponse)
def score_features(payload: ScoreRequest):
    try:
        return service.score_features(
            features=payload.features.model_dump(exclude_none=True),
            session_id=payload.session_id,
            classifier_output=payload.classifier_output,
            confidence=payload.confidence,
            face_count=payload.face_count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/datasets", response_model=list[DatasetFileItem])
def list_datasets():
    return service.list_dataset_files()


@app.get("/api/v1/datasets/{filename}")
def download_dataset(filename: str):
    try:
        file_path = service.resolve_dataset_file(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {filename}") from exc
    return FileResponse(path=file_path, filename=file_path.name, media_type="text/csv")
