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
    GAZE_SIDE_THRESHOLD = 0.32
    GAZE_VERTICAL_THRESHOLD = 0.32
    HEAD_YAW_THRESHOLD = 12.0
    HEAD_PITCH_THRESHOLD = 10.0
    HEAD_ROLL_THRESHOLD = 14.0
    BLINK_LOW = 5.0
    BLINK_HIGH = 30.0
    SPEECH_ACTIVITY_THRESHOLD = 0.45
    MOUTH_OPEN_THRESHOLD = 0.20
    DARK_FRAME_BRIGHTNESS = 35.0
    LOW_CONTRAST_THRESHOLD = 12.0
    TIMESTAMP_FPS_FALLBACK = 30.0

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
    def _resize_for_inference(frame, max_width: int):
        if max_width <= 0:
            return frame
        h, w = frame.shape[:2]
        if w <= max_width:
            return frame
        scale = max_width / float(w)
        resized_h = max(int(h * scale), 1)
        return cv2.resize(
            frame, (max_width, resized_h), interpolation=cv2.INTER_AREA
        )

    @classmethod
    def _severity(cls, value: float, threshold: float):
        magnitude = abs(value)
        if threshold <= 0:
            return "high"
        ratio = magnitude / threshold
        if ratio >= 1.8:
            return "high"
        if ratio >= 1.35:
            return "medium"
        return "low"

    @staticmethod
    def _signal(
        code: str,
        category: str,
        severity: str,
        message: str,
        value: float | None = None,
        threshold: float | None = None,
    ) -> dict:
        return {
            "code": code,
            "category": category,
            "severity": severity,
            "value": value,
            "threshold": threshold,
            "message": message,
        }

    @classmethod
    def _frame_signals(
        cls,
        features,
        face_count: int,
        detected: bool,
        frame_brightness: float | None = None,
        frame_contrast: float | None = None,
    ) -> list[dict]:
        signals = []

        if not detected:
            signals.append(
                cls._signal(
                    code="no_face",
                    category="visibility",
                    severity="high",
                    message="No face detected in this sampled frame.",
                )
            )
            if frame_brightness is not None and frame_contrast is not None:
                if (
                    frame_brightness < cls.DARK_FRAME_BRIGHTNESS
                    and frame_contrast < cls.LOW_CONTRAST_THRESHOLD
                ):
                    signals.append(
                        cls._signal(
                            code="camera_obstructed_or_dark",
                            category="visibility",
                            severity="high",
                            value=round(frame_brightness, 2),
                            threshold=cls.DARK_FRAME_BRIGHTNESS,
                            message=(
                                "Frame is very dark with low contrast; camera may be covered "
                                "or room lighting is too low."
                            ),
                        )
                    )
                elif frame_brightness < cls.DARK_FRAME_BRIGHTNESS:
                    signals.append(
                        cls._signal(
                            code="low_light",
                            category="visibility",
                            severity="medium",
                            value=round(frame_brightness, 2),
                            threshold=cls.DARK_FRAME_BRIGHTNESS,
                            message="Frame is very dark; face visibility is poor.",
                        )
                    )
            return signals

        if face_count > 1:
            signals.append(
                cls._signal(
                    code="multiple_faces",
                    category="identity",
                    severity="high",
                    value=float(face_count),
                    threshold=1.0,
                    message=f"Multiple faces detected ({face_count}).",
                )
            )

        if not features:
            return signals

        gaze_x = float(features.get("gaze_x", 0.0))
        gaze_y = float(features.get("gaze_y", 0.0))
        head_yaw = float(features.get("head_yaw", 0.0))
        head_pitch = float(features.get("head_pitch", 0.0))
        head_roll = float(features.get("head_roll", 0.0))
        blink_rate = float(features.get("blink_rate", 0.0))
        speech_activity = features.get("speech_activity")
        mouth_mar = features.get("mouth_mar")

        if abs(gaze_x) > cls.GAZE_SIDE_THRESHOLD:
            direction = "right" if gaze_x > 0 else "left"
            signals.append(
                cls._signal(
                    code=f"gaze_side_{direction}",
                    category="eyes",
                    severity=cls._severity(gaze_x, cls.GAZE_SIDE_THRESHOLD),
                    value=round(gaze_x, 4),
                    threshold=cls.GAZE_SIDE_THRESHOLD,
                    message=f"Eyes shifted sideways toward the {direction}.",
                )
            )

        if abs(gaze_y) > cls.GAZE_VERTICAL_THRESHOLD:
            direction = "down" if gaze_y > 0 else "up"
            signals.append(
                cls._signal(
                    code=f"gaze_vertical_{direction}",
                    category="eyes",
                    severity=cls._severity(gaze_y, cls.GAZE_VERTICAL_THRESHOLD),
                    value=round(gaze_y, 4),
                    threshold=cls.GAZE_VERTICAL_THRESHOLD,
                    message=f"Eyes shifted {direction}.",
                )
            )

        if abs(head_yaw) > cls.HEAD_YAW_THRESHOLD:
            direction = "right" if head_yaw > 0 else "left"
            signals.append(
                cls._signal(
                    code=f"head_turn_{direction}",
                    category="head_pose",
                    severity=cls._severity(head_yaw, cls.HEAD_YAW_THRESHOLD),
                    value=round(head_yaw, 2),
                    threshold=cls.HEAD_YAW_THRESHOLD,
                    message=f"Head turned toward the {direction}.",
                )
            )

        if abs(head_pitch) > cls.HEAD_PITCH_THRESHOLD:
            direction = "down" if head_pitch > 0 else "up"
            signals.append(
                cls._signal(
                    code=f"head_pitch_{direction}",
                    category="head_pose",
                    severity=cls._severity(head_pitch, cls.HEAD_PITCH_THRESHOLD),
                    value=round(head_pitch, 2),
                    threshold=cls.HEAD_PITCH_THRESHOLD,
                    message=f"Head tilted {direction}.",
                )
            )

        if abs(head_roll) > cls.HEAD_ROLL_THRESHOLD:
            direction = "right" if head_roll > 0 else "left"
            signals.append(
                cls._signal(
                    code=f"head_roll_{direction}",
                    category="head_pose",
                    severity=cls._severity(head_roll, cls.HEAD_ROLL_THRESHOLD),
                    value=round(head_roll, 2),
                    threshold=cls.HEAD_ROLL_THRESHOLD,
                    message=f"Head leaning toward the {direction}.",
                )
            )

        if 0 < blink_rate < cls.BLINK_LOW:
            signals.append(
                cls._signal(
                    code="blink_low",
                    category="eyes",
                    severity="low",
                    value=round(blink_rate, 2),
                    threshold=cls.BLINK_LOW,
                    message="Blink rate is unusually low.",
                )
            )
        elif blink_rate > cls.BLINK_HIGH:
            signals.append(
                cls._signal(
                    code="blink_high",
                    category="eyes",
                    severity="low",
                    value=round(blink_rate, 2),
                    threshold=cls.BLINK_HIGH,
                    message="Blink rate is unusually high.",
                )
            )

        if speech_activity is not None and float(speech_activity) >= cls.SPEECH_ACTIVITY_THRESHOLD:
            speech_value = float(speech_activity)
            signals.append(
                cls._signal(
                    code="speaking_activity",
                    category="mouth",
                    severity=cls._severity(speech_value, cls.SPEECH_ACTIVITY_THRESHOLD),
                    value=round(speech_value, 4),
                    threshold=cls.SPEECH_ACTIVITY_THRESHOLD,
                    message="Likely speaking or active mouth movement detected.",
                )
            )

        if mouth_mar is not None and float(mouth_mar) >= cls.MOUTH_OPEN_THRESHOLD:
            signals.append(
                cls._signal(
                    code="mouth_open",
                    category="mouth",
                    severity="low",
                    value=round(float(mouth_mar), 4),
                    threshold=cls.MOUTH_OPEN_THRESHOLD,
                    message="Mouth appears open.",
                )
            )

        return signals

    @staticmethod
    def _frame_observations(signals: list[dict], label: str, detected: bool) -> list[str]:
        if signals:
            return [signal["message"] for signal in signals]
        if not detected:
            return ["No face detected in this sampled frame."]
        if label == "NORMAL":
            return ["Posture, gaze, and mouth activity look normal in this sampled frame."]
        if label == "CAUTION":
            return ["Mildly unusual behavior detected in this sampled frame."]
        return ["Suspicious behavior detected in this sampled frame."]

    @staticmethod
    def _resolve_timestamp_seconds(
        capture,
        frame_index: int,
        timestamp_fps: float,
        previous_timestamp: float,
    ) -> float:
        pos_msec = float(capture.get(cv2.CAP_PROP_POS_MSEC) or 0.0)
        if pos_msec > 0:
            timestamp = pos_msec / 1000.0
        else:
            timestamp = frame_index / timestamp_fps if timestamp_fps > 0 else previous_timestamp
        return round(max(timestamp, previous_timestamp), 2)

    @staticmethod
    def _event_reason(frame_result: dict) -> tuple[str, str | None]:
        signals = frame_result.get("signals") or []
        if signals:
            return signals[0]["message"], signals[0]["code"]
        observations = frame_result.get("observations") or []
        if observations:
            return observations[0], None
        return "Suspicious activity detected.", None

    def _build_events(self, frame_results: list[dict]) -> list[dict]:
        events = []
        current_event = None

        def flush():
            nonlocal current_event
            if not current_event:
                return
            current_event["duration_seconds"] = round(
                max(
                    current_event["end_timestamp_seconds"]
                    - current_event["start_timestamp_seconds"],
                    0.0,
                ),
                2,
            )
            events.append(current_event)
            current_event = None

        for frame in frame_results:
            signals = frame.get("signals") or []
            should_track = frame["label"] != "NORMAL" or bool(signals)
            if not should_track:
                flush()
                continue

            reason, signal_code = self._event_reason(frame)
            frame_start = float(frame.get("timestamp_seconds", 0.0))
            frame_window = float(frame.get("sample_window_seconds") or 0.0)
            frame_end = round(max(frame_start + frame_window, frame_start), 2)
            frame_label = frame["label"] if frame["label"] != "NORMAL" else "CAUTION"

            can_extend = (
                current_event
                and current_event["label"] == frame_label
                and current_event["signal_code"] == signal_code
                and frame_start
                <= current_event["end_timestamp_seconds"] + max(frame_window, 0.05)
            )

            if can_extend:
                current_event["end_timestamp_seconds"] = max(
                    current_event["end_timestamp_seconds"], frame_end
                )
                current_event["end_frame_index"] = frame["frame_index"]
                current_event["frame_count"] += 1
                frame_score = frame.get("score")
                if frame_score is not None:
                    if current_event["max_score"] is None:
                        current_event["max_score"] = frame_score
                    else:
                        current_event["max_score"] = max(
                            current_event["max_score"], frame_score
                        )
                continue

            flush()
            current_event = {
                "start_timestamp_seconds": frame_start,
                "end_timestamp_seconds": frame_end,
                "duration_seconds": 0.0,
                "start_frame_index": frame["frame_index"],
                "end_frame_index": frame["frame_index"],
                "label": frame_label,
                "reason": reason,
                "signal_code": signal_code,
                "max_score": frame.get("score"),
                "frame_count": 1,
            }

        flush()
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
            signals = self._frame_signals(
                features=None,
                face_count=face_count,
                detected=False,
                frame_brightness=None,
                frame_contrast=None,
            )
            return {
                "detected": False,
                "face_count": face_count,
                "session_id": session_id,
                "features": None,
                "score": None,
                "label": "NO_FACE",
                "label_color": [220, 0, 0],
                "observations": self._frame_observations(
                    signals=signals, label="NO_FACE", detected=False
                ),
                "signals": signals,
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

        signals = self._frame_signals(
            features=features,
            face_count=face_count,
            detected=True,
            frame_brightness=None,
            frame_contrast=None,
        )
        observations = self._frame_observations(
            signals=signals, label=label, detected=True
        )

        return {
            "detected": True,
            "face_count": face_count,
            "session_id": active_session_id,
            "features": features,
            "score": score,
            "label": label,
            "label_color": list(colour),
            "observations": observations,
            "signals": signals,
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
        include_landmarks: bool = False,
        inference_max_width: int = 640,
    ) -> dict:
        self._validate_classifier_inputs(classifier_output, confidence)
        if sample_every_n_frames < 1:
            raise ValueError("sample_every_n_frames must be at least 1.")
        if max_frames < 1:
            raise ValueError("max_frames must be at least 1.")
        if inference_max_width < 160:
            raise ValueError("inference_max_width must be at least 160.")

        suffix = Path(filename).suffix or ".mp4"
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(video_bytes)
                temp_path = temp_file.name

            capture = cv2.VideoCapture(temp_path)
            if not capture.isOpened():
                raise ValueError("Uploaded file is not a valid video.")

            raw_fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
            fps = round(raw_fps, 2) if raw_fps > 0 else 0.0
            timestamp_fps = raw_fps if raw_fps > 0 else self.TIMESTAMP_FPS_FALLBACK
            timestamp_source = "video_fps" if raw_fps > 0 else "estimated_30fps"

            total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            duration_seconds = (
                round(total_frames / raw_fps, 2) if raw_fps > 0 and total_frames > 0 else 0.0
            )
            sample_window_seconds = round(
                max(sample_every_n_frames / timestamp_fps, 1.0 / timestamp_fps), 2
            )

            active_session_id, extractor, scorer = self._get_processors(session_id)
            renderer = FaceMeshRenderer(static_image_mode=False, max_num_faces=2)
            frame_results = []
            frames_processed = 0
            frames_sampled = 0
            last_timestamp_seconds = 0.0

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
                    inference_frame = self._resize_for_inference(
                        frame, max_width=inference_max_width
                    )
                    gray = cv2.cvtColor(inference_frame, cv2.COLOR_BGR2GRAY)
                    frame_brightness = float(np.mean(gray))
                    frame_contrast = float(np.std(gray))

                    renderer.find_face(inference_frame, draw=False)
                    landmarks = renderer.find_landmarks(inference_frame, draw=False)

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

                    timestamp_seconds = self._resolve_timestamp_seconds(
                        capture=capture,
                        frame_index=frame_index,
                        timestamp_fps=timestamp_fps,
                        previous_timestamp=last_timestamp_seconds,
                    )
                    last_timestamp_seconds = timestamp_seconds

                    signals = self._frame_signals(
                        features=features,
                        face_count=renderer.face_count,
                        detected=detected,
                        frame_brightness=frame_brightness,
                        frame_contrast=frame_contrast,
                    )
                    observations = self._frame_observations(
                        signals=signals, label=label, detected=detected
                    )
                    frame_results.append(
                        {
                            "frame_index": frame_index,
                            "timestamp_seconds": timestamp_seconds,
                            "sample_window_seconds": sample_window_seconds,
                            "timestamp_source": timestamp_source,
                            "detected": detected,
                            "face_count": renderer.face_count,
                            "score": score,
                            "label": label,
                            "label_color": list(colour),
                            "observations": observations,
                            "signals": signals,
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

            has_suspicious = any(item["label"] == "SUSPICIOUS" for item in frame_results)
            has_caution = any(item["label"] == "CAUTION" for item in frame_results)
            has_signals = any(item.get("signals") for item in frame_results)
            all_no_face = all(item["label"] == "NO_FACE" for item in frame_results)
            if has_suspicious:
                final_label = "SUSPICIOUS"
            elif all_no_face:
                final_label = "NO_FACE"
            elif has_caution or has_signals:
                final_label = "CAUTION"
            else:
                final_label = "NORMAL"

            events = self._build_events(frame_results)

            if duration_seconds <= 0 and total_frames > 0:
                duration_seconds = round(total_frames / timestamp_fps, 2)
            if duration_seconds <= 0:
                last_frame = frame_results[-1]
                duration_seconds = round(
                    last_frame["timestamp_seconds"]
                    + float(last_frame.get("sample_window_seconds") or 0.0),
                    2,
                )

            return {
                "session_id": active_session_id,
                "filename": filename,
                "frames_processed": frames_processed,
                "frames_sampled": frames_sampled,
                "fps": fps,
                "timestamp_source": timestamp_source,
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
                "signals": frame.get("signals") or [],
            }
            for frame in ranked_frames[:max_key_frames]
        ]

        return {
            "session_id": analysis_result["session_id"],
            "filename": analysis_result["filename"],
            "frames_processed": analysis_result["frames_processed"],
            "frames_sampled": analysis_result["frames_sampled"],
            "fps": analysis_result["fps"],
            "timestamp_source": analysis_result["timestamp_source"],
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

        signals = self._frame_signals(
            features=features,
            face_count=face_count,
            detected=True,
            frame_brightness=None,
            frame_contrast=None,
        )
        observations = self._frame_observations(
            signals=signals, label=label, detected=True
        )

        return {
            "session_id": active_session_id,
            "face_count": face_count,
            "score": score,
            "label": label,
            "label_color": list(colour),
            "features": features,
            "observations": observations,
            "signals": signals,
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
