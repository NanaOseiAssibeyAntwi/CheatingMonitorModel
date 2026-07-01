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
    HEAD_PITCH_DOWN_THRESHOLD = 10.0
    HEAD_PITCH_UP_THRESHOLD = 16.0
    HEAD_ROLL_THRESHOLD = 14.0
    BLINK_LOW = 5.0
    BLINK_HIGH = 30.0
    MOUTH_OPEN_THRESHOLD = 0.24
    DARK_FRAME_BRIGHTNESS = 35.0
    LOW_CONTRAST_THRESHOLD = 12.0
    TIMESTAMP_FPS_FALLBACK = 30.0
    TRANSIENT_SIGNAL_RULES: dict[str, tuple[int, float]] = {
        "no_face": (2, 1.2),
        "multiple_faces": (2, 1.2),
    }

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
    def _severity_rank(severity: str | None) -> int:
        ranks = {"low": 1, "medium": 2, "high": 3}
        return ranks.get((severity or "").lower(), 0)

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

        if head_pitch > cls.HEAD_PITCH_DOWN_THRESHOLD:
            signals.append(
                cls._signal(
                    code="head_pitch_down",
                    category="head_pose",
                    severity=cls._severity(head_pitch, cls.HEAD_PITCH_DOWN_THRESHOLD),
                    value=round(head_pitch, 2),
                    threshold=cls.HEAD_PITCH_DOWN_THRESHOLD,
                    message="Head tilted down.",
                )
            )
        elif head_pitch < -cls.HEAD_PITCH_UP_THRESHOLD:
            signals.append(
                cls._signal(
                    code="head_pitch_up",
                    category="head_pose",
                    severity=cls._severity(head_pitch, cls.HEAD_PITCH_UP_THRESHOLD),
                    value=round(head_pitch, 2),
                    threshold=cls.HEAD_PITCH_UP_THRESHOLD,
                    message="Head tilted up.",
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

        if (
            mouth_mar is not None
            and float(mouth_mar) >= (cls.MOUTH_OPEN_THRESHOLD + 0.06)
        ):
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

    @classmethod
    def _top_signals(cls, signals: list[dict], limit: int = 2) -> list[dict]:
        if limit < 1:
            return []
        ranked = sorted(
            signals,
            key=lambda signal: (
                cls._severity_rank(signal.get("severity")),
                signal.get("value") is not None,
                abs(float(signal.get("value") or 0.0)),
            ),
            reverse=True,
        )
        return ranked[:limit]

    @classmethod
    def _frame_observations(cls, signals: list[dict], label: str, detected: bool) -> list[str]:
        if signals:
            return [signal["message"] for signal in cls._top_signals(signals, limit=2)]
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
    def _build_sample_indices(
        total_frames: int, sample_every_n_frames: int, max_frames: int
    ) -> list[int]:
        if total_frames <= 0:
            return []

        base_indices = list(range(0, total_frames, sample_every_n_frames))
        if not base_indices:
            return [0]
        if len(base_indices) <= max_frames:
            return base_indices
        if max_frames == 1:
            return [base_indices[0]]

        last_position = len(base_indices) - 1
        selected_positions = [
            (i * last_position) // (max_frames - 1) for i in range(max_frames)
        ]
        return [base_indices[position] for position in selected_positions]

    @staticmethod
    def _finalize_event(event: dict) -> dict:
        event["duration_seconds"] = round(
            max(
                event["end_timestamp_seconds"] - event["start_timestamp_seconds"],
                0.0,
            ),
            2,
        )
        return event

    @staticmethod
    def _fallback_event_from_frame(
        frame: dict, frame_start: float, frame_end: float
    ) -> dict | None:
        label = frame.get("label")
        if label not in {"CAUTION", "SUSPICIOUS"}:
            return None
        severity = "high" if label == "SUSPICIOUS" else "medium"
        return {
            "start_timestamp_seconds": frame_start,
            "end_timestamp_seconds": frame_end,
            "duration_seconds": 0.0,
            "start_frame_index": frame["frame_index"],
            "end_frame_index": frame["frame_index"],
            "label": label,
            "severity": severity,
            "reason": "Suspicion score remained elevated.",
            "signal_code": "risk_score",
            "max_score": frame.get("score"),
            "frame_count": 1,
        }

    @classmethod
    def _is_transient_event(cls, event: dict) -> bool:
        signal_code = event.get("signal_code")
        if not signal_code:
            return False
        rule = cls.TRANSIENT_SIGNAL_RULES.get(signal_code)
        if not rule:
            return False
        min_frames, min_duration = rule
        frame_count = int(event.get("frame_count") or 0)
        duration_seconds = float(event.get("duration_seconds") or 0.0)
        return frame_count < min_frames and duration_seconds < min_duration

    def _build_events(self, frame_results: list[dict]) -> list[dict]:
        events = []
        active_events_by_code: dict[str, dict] = {}

        for frame in frame_results:
            frame_start = float(frame.get("timestamp_seconds", 0.0))
            frame_window = float(frame.get("sample_window_seconds") or 0.0)
            frame_end = round(max(frame_start + frame_window, frame_start), 2)
            frame_score = frame.get("score")

            frame_signals = self._top_signals(frame.get("signals") or [], limit=3)
            seen_codes = set()

            for signal in frame_signals:
                signal_code = signal.get("code") or "unknown_signal"
                seen_codes.add(signal_code)
                severity = signal.get("severity") or "medium"
                frame_label = (
                    "SUSPICIOUS"
                    if frame.get("label") == "SUSPICIOUS" or severity == "high"
                    else "CAUTION"
                )

                current_event = active_events_by_code.get(signal_code)
                can_extend = (
                    current_event
                    and frame_start
                    <= current_event["end_timestamp_seconds"] + max(frame_window, 0.05)
                )
                if can_extend:
                    current_event["end_timestamp_seconds"] = max(
                        current_event["end_timestamp_seconds"], frame_end
                    )
                    current_event["end_frame_index"] = frame["frame_index"]
                    current_event["frame_count"] += 1
                    current_event["label"] = (
                        "SUSPICIOUS"
                        if current_event["label"] == "SUSPICIOUS"
                        or frame_label == "SUSPICIOUS"
                        else "CAUTION"
                    )
                    if frame_score is not None:
                        if current_event["max_score"] is None:
                            current_event["max_score"] = frame_score
                        else:
                            current_event["max_score"] = max(
                                current_event["max_score"], frame_score
                            )
                    continue

                if current_event:
                    events.append(self._finalize_event(current_event))

                active_events_by_code[signal_code] = {
                    "start_timestamp_seconds": frame_start,
                    "end_timestamp_seconds": frame_end,
                    "duration_seconds": 0.0,
                    "start_frame_index": frame["frame_index"],
                    "end_frame_index": frame["frame_index"],
                    "label": frame_label,
                    "severity": severity,
                    "reason": signal.get("message") or "Suspicious activity detected.",
                    "signal_code": signal_code,
                    "max_score": frame_score,
                    "frame_count": 1,
                }

            fallback_event = self._fallback_event_from_frame(frame, frame_start, frame_end)
            if fallback_event and not frame_signals:
                fallback_code = fallback_event["signal_code"]
                if fallback_code not in seen_codes:
                    seen_codes.add(fallback_code)
                    current_event = active_events_by_code.get(fallback_code)
                    can_extend = (
                        current_event
                        and frame_start
                        <= current_event["end_timestamp_seconds"] + max(frame_window, 0.05)
                    )
                    if can_extend:
                        current_event["end_timestamp_seconds"] = max(
                            current_event["end_timestamp_seconds"], frame_end
                        )
                        current_event["end_frame_index"] = frame["frame_index"]
                        current_event["frame_count"] += 1
                        if frame_score is not None:
                            if current_event["max_score"] is None:
                                current_event["max_score"] = frame_score
                            else:
                                current_event["max_score"] = max(
                                    current_event["max_score"], frame_score
                                )
                    else:
                        if current_event:
                            events.append(self._finalize_event(current_event))
                        active_events_by_code[fallback_code] = fallback_event

            stale_codes = [
                code for code in active_events_by_code.keys() if code not in seen_codes
            ]
            for stale_code in stale_codes:
                events.append(self._finalize_event(active_events_by_code.pop(stale_code)))

        for remaining_code in list(active_events_by_code.keys()):
            events.append(self._finalize_event(active_events_by_code.pop(remaining_code)))

        events.sort(
            key=lambda event: (
                float(event.get("start_timestamp_seconds") or 0.0),
                event.get("signal_code") or "",
            )
        )
        return [event for event in events if not self._is_transient_event(event)]

    def _target_alert_count(self, events: list[dict], max_alerts: int) -> int:
        if not events or max_alerts < 1:
            return 0
        distinct_signal_count = len(
            {event.get("signal_code") or f"label:{event.get('label')}" for event in events}
        )
        total_events = len(events)

        target = 1
        if distinct_signal_count >= 2 or total_events >= 4:
            target = 2
        if distinct_signal_count >= 3 or total_events >= 7:
            target = 3
        return min(target, max_alerts)

    def _build_alerts(self, events: list[dict], max_alerts: int = 3) -> list[dict]:
        target_alerts = self._target_alert_count(events, max_alerts=max_alerts)
        if target_alerts < 1:
            return []

        ranked_events = sorted(
            events,
            key=lambda event: (
                self._severity_rank(event.get("severity")),
                1 if event.get("label") == "SUSPICIOUS" else 0,
                float(event.get("duration_seconds") or 0.0),
                float(event.get("max_score") or 0.0),
            ),
            reverse=True,
        )

        selected_events = []
        selected_event_ids = set()
        seen_signal_codes = set()
        for event in ranked_events:
            signal_code = event.get("signal_code") or f"label:{event.get('label')}"
            if signal_code in seen_signal_codes:
                continue
            selected_events.append(event)
            selected_event_ids.add(id(event))
            seen_signal_codes.add(signal_code)
            if len(selected_events) >= target_alerts:
                break

        if len(selected_events) < target_alerts:
            for event in ranked_events:
                if id(event) in selected_event_ids:
                    continue
                selected_events.append(event)
                selected_event_ids.add(id(event))
                if len(selected_events) >= target_alerts:
                    break

        alerts = []
        for event in selected_events:
            alerts.append(
                {
                    "start_timestamp_seconds": event["start_timestamp_seconds"],
                    "end_timestamp_seconds": event["end_timestamp_seconds"],
                    "duration_seconds": event["duration_seconds"],
                    "label": event["label"],
                    "severity": event.get("severity") or "medium",
                    "reason": event["reason"],
                    "signal_code": event.get("signal_code"),
                }
            )
        return alerts

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
        compact_signals = self._top_signals(signals, limit=3)

        return {
            "detected": True,
            "face_count": face_count,
            "session_id": active_session_id,
            "features": features,
            "score": score,
            "label": label,
            "label_color": list(colour),
            "observations": observations,
            "signals": compact_signals,
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
        include_frame_results: bool = False,
        max_alerts: int = 3,
    ) -> dict:
        self._validate_classifier_inputs(classifier_output, confidence)
        if sample_every_n_frames < 1:
            raise ValueError("sample_every_n_frames must be at least 1.")
        if max_frames < 1:
            raise ValueError("max_frames must be at least 1.")
        if inference_max_width < 160:
            raise ValueError("inference_max_width must be at least 160.")
        if max_alerts < 1:
            raise ValueError("max_alerts must be at least 1.")

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
            sample_indices = self._build_sample_indices(
                total_frames=total_frames,
                sample_every_n_frames=sample_every_n_frames,
                max_frames=max_frames,
            )
            sample_windows_by_index: dict[int, float] = {}
            if sample_indices:
                for index, frame_index in enumerate(sample_indices):
                    if index + 1 < len(sample_indices):
                        next_frame_index = sample_indices[index + 1]
                    else:
                        next_frame_index = min(
                            frame_index + sample_every_n_frames, total_frames
                        )
                    delta_frames = max(next_frame_index - frame_index, 1)
                    sample_windows_by_index[frame_index] = round(
                        max(delta_frames / timestamp_fps, 1.0 / timestamp_fps),
                        2,
                    )

            active_session_id, extractor, scorer = self._get_processors(session_id)
            renderer = FaceMeshRenderer(static_image_mode=False, max_num_faces=2)
            fallback_renderer = FaceMeshRenderer(static_image_mode=True, max_num_faces=2)
            frame_results = []
            frames_processed = 0
            frames_sampled = 0
            last_timestamp_seconds = 0.0
            sample_index_cursor = 0

            try:
                while True:
                    if sample_indices and sample_index_cursor >= len(sample_indices):
                        break
                    if not sample_indices and frames_sampled >= max_frames:
                        break

                    success, frame = capture.read()
                    if not success:
                        break

                    frame_index = frames_processed
                    frames_processed += 1

                    if sample_indices:
                        target_frame_index = sample_indices[sample_index_cursor]
                        if frame_index < target_frame_index:
                            continue
                        if frame_index > target_frame_index:
                            while (
                                sample_index_cursor < len(sample_indices)
                                and sample_indices[sample_index_cursor] < frame_index
                            ):
                                sample_index_cursor += 1
                            if sample_index_cursor >= len(sample_indices):
                                break
                            if frame_index != sample_indices[sample_index_cursor]:
                                continue
                        sample_index_cursor += 1
                    elif frame_index % sample_every_n_frames != 0:
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
                    frame_face_count = renderer.face_count
                    if not landmarks:
                        fallback_renderer.find_face(inference_frame, draw=False)
                        fallback_landmarks = fallback_renderer.find_landmarks(
                            inference_frame, draw=False
                        )
                        if fallback_landmarks:
                            landmarks = fallback_landmarks
                            frame_face_count = fallback_renderer.face_count

                    if landmarks:
                        features = extractor.extract(landmarks)
                        score, label, colour = scorer.update(
                            features=features,
                            classifier_output=classifier_output,
                            confidence=confidence,
                        )
                        if frame_face_count > 1:
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
                        frame_face_count = 0

                    timestamp_seconds = self._resolve_timestamp_seconds(
                        capture=capture,
                        frame_index=frame_index,
                        timestamp_fps=timestamp_fps,
                        previous_timestamp=last_timestamp_seconds,
                    )
                    last_timestamp_seconds = timestamp_seconds

                    signals = self._frame_signals(
                        features=features,
                        face_count=frame_face_count,
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
                            "sample_window_seconds": sample_windows_by_index.get(
                                frame_index, sample_window_seconds
                            ),
                            "timestamp_source": timestamp_source,
                            "detected": detected,
                            "face_count": frame_face_count,
                            "score": score,
                            "label": label,
                            "label_color": list(colour),
                            "observations": observations,
                            "signals": self._top_signals(signals, limit=3),
                            "features": features,
                            "landmarks": normalized_landmarks,
                        }
                    )
            finally:
                capture.release()
                renderer.close()
                fallback_renderer.close()

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
            alerts = self._build_alerts(events, max_alerts=max_alerts)

            if duration_seconds <= 0 and total_frames > 0:
                duration_seconds = round(total_frames / timestamp_fps, 2)
            if duration_seconds <= 0:
                last_frame = frame_results[-1]
                duration_seconds = round(
                    last_frame["timestamp_seconds"]
                    + float(last_frame.get("sample_window_seconds") or 0.0),
                    2,
                )
            output_frame_results = frame_results if include_frame_results else []

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
                "alerts": alerts,
                "frame_results": output_frame_results,
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
                "signals": AnalysisService._top_signals(frame.get("signals") or [], limit=2),
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
            "alerts": analysis_result.get("alerts", []),
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
        compact_signals = self._top_signals(signals, limit=3)

        return {
            "session_id": active_session_id,
            "face_count": face_count,
            "score": score,
            "label": label,
            "label_color": list(colour),
            "features": features,
            "observations": observations,
            "signals": compact_signals,
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
