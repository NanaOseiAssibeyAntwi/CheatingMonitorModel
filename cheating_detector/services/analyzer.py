from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from cheating_detector.core.face_mesh_renderer import FaceMeshRenderer
from cheating_detector.core.feature_extractor import FeatureExtractor
from cheating_detector.core.suspicion_scorer import SuspicionScorer
from cheating_detector.services.sessions import SessionStore
from cheating_detector.settings import DATASET_DIR


class AnalysisService:
    def __init__(self, session_store: SessionStore | None = None):
        self.session_store = session_store or SessionStore()

    @staticmethod
    def _validate_classifier_inputs(
        classifier_output: int | None, confidence: float
    ) -> None:
        if classifier_output not in (None, 0, 1):
            raise ValueError("classifier_output must be 0, 1, or null.")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0.")

    def create_session(self) -> str:
        return self.session_store.create()

    def _get_processors(self, session_id: str | None):
        active_session_id = session_id
        if session_id:
            active_session_id, session = self.session_store.get_or_create(session_id)
            return active_session_id, session.extractor, session.scorer
        return None, FeatureExtractor(), SuspicionScorer()

    @staticmethod
    def _landmark_points(landmarks) -> list[dict]:
        points = []
        for item in landmarks:
            points.append(
                {
                    "id": int(item[0]),
                    "pixel_x": int(item[1]),
                    "pixel_y": int(item[2]),
                    "x": float(item[3]),
                    "y": float(item[4]),
                    "z": float(item[5]),
                }
            )
        return points

    @staticmethod
    def _frame_observations(features, face_count: int, detected: bool, label: str) -> list[str]:
        observations = []
        if not detected:
            return ["No face detected in this sampled frame."]
        if face_count > 1:
            observations.append("Multiple faces detected.")
        if not features:
            return observations or ["Face detected, but no features were extracted."]

        if abs(features["gaze_x"]) > 0.35:
            direction = "right" if features["gaze_x"] > 0 else "left"
            observations.append(f"Looking sideways toward the {direction}.")
        if abs(features["gaze_y"]) > 0.40:
            direction = "down" if features["gaze_y"] > 0 else "up"
            observations.append(f"Eyes shifted {direction}.")
        if abs(features["head_yaw"]) > 20.0:
            direction = "right" if features["head_yaw"] > 0 else "left"
            observations.append(f"Head turned strongly to the {direction}.")
        if abs(features["head_pitch"]) > 25.0:
            direction = "down" if features["head_pitch"] > 0 else "up"
            observations.append(f"Head tilted {direction}.")
        if abs(features["head_roll"]) > 18.0:
            direction = "right" if features["head_roll"] > 0 else "left"
            observations.append(f"Head leaning to the {direction}.")
        if features["blink_rate"] < 5.0:
            observations.append("Blink rate is unusually low.")
        elif features["blink_rate"] > 30.0:
            observations.append("Blink rate is unusually high.")

        if not observations:
            if label == "NORMAL":
                observations.append("Posture and gaze look normal in this sampled frame.")
            elif label == "CAUTION":
                observations.append("Mildly unusual behavior detected in this sampled frame.")
            else:
                observations.append("Suspicious behavior detected in this sampled frame.")
        return observations

    @staticmethod
    def _event_reason(frame_result: dict) -> str:
        if frame_result["observations"]:
            return frame_result["observations"][0]
        return "Suspicious activity detected."

    def _build_events(self, frame_results: list[dict]) -> list[dict]:
        events = []
        current_event = None

        for frame in frame_results:
            if frame["label"] not in {"CAUTION", "SUSPICIOUS"}:
                if current_event:
                    events.append(current_event)
                    current_event = None
                continue

            reason = self._event_reason(frame)
            if (
                current_event
                and current_event["label"] == frame["label"]
                and current_event["reason"] == reason
            ):
                current_event["end_timestamp_seconds"] = frame["timestamp_seconds"]
                current_event["end_frame_index"] = frame["frame_index"]
                current_event["frame_count"] += 1
                current_event["max_score"] = max(
                    current_event["max_score"] or 0, frame["score"] or 0
                )
            else:
                if current_event:
                    events.append(current_event)
                current_event = {
                    "start_timestamp_seconds": frame["timestamp_seconds"],
                    "end_timestamp_seconds": frame["timestamp_seconds"],
                    "start_frame_index": frame["frame_index"],
                    "end_frame_index": frame["frame_index"],
                    "label": frame["label"],
                    "reason": reason,
                    "max_score": frame["score"],
                    "frame_count": 1,
                }

        if current_event:
            events.append(current_event)

        return events

    def reset_session(self, session_id: str) -> bool:
        return self.session_store.reset(session_id)

    def delete_session(self, session_id: str) -> bool:
        return self.session_store.delete(session_id)

    def analyze_image_bytes(
        self,
        image_bytes: bytes,
        session_id: str | None = None,
        classifier_output: int | None = None,
        confidence: float = 1.0,
    ) -> dict:
        self._validate_classifier_inputs(classifier_output, confidence)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Uploaded file is not a valid image.")

        renderer = FaceMeshRenderer(static_image_mode=True, max_num_faces=2)
        try:
            renderer.find_face(frame, draw=False)
            landmarks = renderer.find_landmarks(frame, draw=False)
            return self.analyze_landmarks(
                landmarks=landmarks,
                face_count=renderer.face_count,
                session_id=session_id,
                classifier_output=classifier_output,
                confidence=confidence,
            )
        finally:
            renderer.close()

    def analyze_landmarks(
        self,
        landmarks,
        face_count: int = 1,
        session_id: str | None = None,
        classifier_output: int | None = None,
        confidence: float = 1.0,
    ) -> dict:
        self._validate_classifier_inputs(classifier_output, confidence)
        if not landmarks:
            return {
                "detected": False,
                "face_count": face_count,
                "session_id": session_id,
                "features": None,
                "score": None,
                "label": "NO_FACE",
                "label_color": [220, 0, 0],
            }

        active_session_id, extractor, scorer = self._get_processors(session_id)

        features = extractor.extract(landmarks)
        if not features:
            raise ValueError("Could not extract features from landmarks.")

        score, label, colour = scorer.update(
            features=features,
            classifier_output=classifier_output,
            confidence=confidence,
        )

        if face_count > 1:
            label = "SUSPICIOUS"
            colour = (0, 0, 220)
            score = max(score, 75)

        return {
            "detected": True,
            "face_count": face_count,
            "session_id": active_session_id,
            "features": features,
            "score": score,
            "label": label,
            "label_color": list(colour),
        }

    def analyze_video_bytes(
        self,
        video_bytes: bytes,
        filename: str,
        session_id: str | None = None,
        classifier_output: int | None = None,
        confidence: float = 1.0,
        sample_every_n_frames: int = 10,
        max_frames: int = 30,
        include_landmarks: bool = True,
    ) -> dict:
        self._validate_classifier_inputs(classifier_output, confidence)
        if sample_every_n_frames < 1:
            raise ValueError("sample_every_n_frames must be at least 1.")
        if max_frames < 1:
            raise ValueError("max_frames must be at least 1.")

        suffix = Path(filename).suffix or ".mp4"
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(video_bytes)
                temp_path = temp_file.name

            capture = cv2.VideoCapture(temp_path)
            if not capture.isOpened():
                raise ValueError("Uploaded file is not a valid video.")

            fps = capture.get(cv2.CAP_PROP_FPS)
            fps = round(float(fps), 2) if fps and fps > 0 else 0.0
            total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            duration_seconds = (
                round(total_frames / fps, 2) if fps > 0 and total_frames > 0 else 0.0
            )

            active_session_id, extractor, scorer = self._get_processors(session_id)
            renderer = FaceMeshRenderer(static_image_mode=False, max_num_faces=2)
            frame_results = []
            frames_processed = 0
            frames_sampled = 0

            try:
                while frames_sampled < max_frames:
                    success, frame = capture.read()
                    if not success:
                        break

                    frame_index = frames_processed
                    frames_processed += 1

                    if frame_index % sample_every_n_frames != 0:
                        continue

                    frames_sampled += 1
                    renderer.find_face(frame, draw=False)
                    landmarks = renderer.find_landmarks(frame, draw=False)

                    if landmarks:
                        features = extractor.extract(landmarks)
                        score, label, colour = scorer.update(
                            features=features,
                            classifier_output=classifier_output,
                            confidence=confidence,
                        )
                        if renderer.face_count > 1:
                            label = "SUSPICIOUS"
                            colour = (0, 0, 220)
                            score = max(score, 75)
                        detected = True
                        normalized_landmarks = (
                            self._landmark_points(landmarks) if include_landmarks else None
                        )
                    else:
                        features = None
                        score = None
                        label = "NO_FACE"
                        colour = (220, 0, 0)
                        detected = False
                        normalized_landmarks = None

                    timestamp_seconds = round(frame_index / fps, 2) if fps > 0 else 0.0
                    observations = self._frame_observations(
                        features=features,
                        face_count=renderer.face_count,
                        detected=detected,
                        label=label,
                    )
                    frame_results.append(
                        {
                            "frame_index": frame_index,
                            "timestamp_seconds": timestamp_seconds,
                            "detected": detected,
                            "face_count": renderer.face_count,
                            "score": score,
                            "label": label,
                            "label_color": list(colour),
                            "observations": observations,
                            "features": features,
                            "landmarks": normalized_landmarks,
                        }
                    )
            finally:
                capture.release()
                renderer.close()

            if not frame_results:
                raise ValueError("Could not read any frames from the uploaded video.")

            scored_frames = [
                item["score"] for item in frame_results if item["score"] is not None
            ]
            detections = sum(1 for item in frame_results if item["detected"])
            max_score = max(scored_frames) if scored_frames else 0
            average_score = (
                round(sum(scored_frames) / len(scored_frames), 2)
                if scored_frames
                else 0.0
            )
            final_label = (
                max(frame_results, key=lambda item: item["score"] or -1)["label"]
                if frame_results
                else "NO_FACE"
            )
            events = self._build_events(frame_results)

            return {
                "session_id": active_session_id,
                "filename": filename,
                "frames_processed": frames_processed,
                "frames_sampled": frames_sampled,
                "fps": fps,
                "duration_seconds": duration_seconds,
                "detections": detections,
                "max_score": max_score,
                "average_score": average_score,
                "final_label": final_label,
                "suspicious_event_count": len(events),
                "events": events,
                "frame_results": frame_results,
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    @staticmethod
    def summarize_video_analysis(
        analysis_result: dict, max_key_frames: int = 5
    ) -> dict:
        frame_results = analysis_result.get("frame_results", [])
        ranked_frames = sorted(
            frame_results,
            key=lambda item: (
                item.get("score") is not None,
                item.get("score") or -1,
                item.get("timestamp_seconds") or 0.0,
            ),
            reverse=True,
        )
        key_frames = [
            {
                "frame_index": frame["frame_index"],
                "timestamp_seconds": frame["timestamp_seconds"],
                "label": frame["label"],
                "score": frame["score"],
                "observations": frame["observations"],
            }
            for frame in ranked_frames[:max_key_frames]
        ]

        return {
            "session_id": analysis_result["session_id"],
            "filename": analysis_result["filename"],
            "frames_processed": analysis_result["frames_processed"],
            "frames_sampled": analysis_result["frames_sampled"],
            "fps": analysis_result["fps"],
            "duration_seconds": analysis_result["duration_seconds"],
            "detections": analysis_result["detections"],
            "max_score": analysis_result["max_score"],
            "average_score": analysis_result["average_score"],
            "final_label": analysis_result["final_label"],
            "suspicious_event_count": analysis_result["suspicious_event_count"],
            "events": analysis_result["events"],
            "key_frames": key_frames,
        }

    def score_features(
        self,
        features: dict,
        session_id: str | None = None,
        classifier_output: int | None = None,
        confidence: float = 1.0,
        face_count: int = 1,
    ) -> dict:
        self._validate_classifier_inputs(classifier_output, confidence)
        active_session_id, _, scorer = self._get_processors(session_id)

        score, label, colour = scorer.update(
            features=features,
            classifier_output=classifier_output,
            confidence=confidence,
        )
        if face_count > 1:
            label = "SUSPICIOUS"
            colour = (0, 0, 220)
            score = max(score, 75)

        return {
            "session_id": active_session_id,
            "face_count": face_count,
            "score": score,
            "label": label,
            "label_color": list(colour),
            "features": features,
        }

    def normalize_landmarks(self, landmarks) -> list[list[float]]:
        normalized = []
        for landmark in landmarks:
            normalized.append(
                [
                    landmark.id,
                    getattr(landmark, "pixel_x", 0),
                    getattr(landmark, "pixel_y", 0),
                    landmark.x,
                    landmark.y,
                    landmark.z,
                ]
            )
        return normalized

    def list_dataset_files(self) -> list[dict]:
        DATASET_DIR.mkdir(parents=True, exist_ok=True)
        files = []
        for file_path in sorted(DATASET_DIR.glob("*.csv")):
            stat = file_path.stat()
            files.append(
                {
                    "name": file_path.name,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
            )
        return files

    def resolve_dataset_file(self, filename: str) -> Path:
        candidate = (DATASET_DIR / filename).resolve()
        dataset_root = DATASET_DIR.resolve()
        if dataset_root not in candidate.parents and candidate != dataset_root:
            raise ValueError("Invalid dataset filename.")
        if not candidate.exists() or candidate.suffix.lower() != ".csv":
            raise FileNotFoundError(filename)
        return candidate
