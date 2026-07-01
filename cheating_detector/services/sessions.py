from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

from cheating_detector.core.feature_extractor import FeatureExtractor
from cheating_detector.core.suspicion_scorer import SuspicionScorer


@dataclass
class AnalysisSession:
    extractor: FeatureExtractor = field(
        default_factory=lambda: FeatureExtractor(auto_calibrate=True, calibration_frames=40)
    )
    scorer: SuspicionScorer = field(default_factory=SuspicionScorer)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def touch(self):
        self.updated_at = time.time()


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, AnalysisSession] = {}
        self._lock = threading.Lock()

    def create(self) -> str:
        session_id = uuid.uuid4().hex
        with self._lock:
            self._sessions[session_id] = AnalysisSession()
        return session_id

    def get(self, session_id: str) -> AnalysisSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.touch()
            return session

    def get_or_create(self, session_id: str | None):
        if session_id:
            session = self.get(session_id)
            if session:
                return session_id, session
        new_session_id = self.create()
        return new_session_id, self.get(new_session_id)

    def reset(self, session_id: str) -> bool:
        with self._lock:
            if session_id not in self._sessions:
                return False
            self._sessions[session_id] = AnalysisSession()
            return True

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None
