import unittest
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

import cv2
import numpy as np
from fastapi.testclient import TestClient

from cheating_detector.api.app import app
from cheating_detector.services.analyzer import AnalysisService

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.",
)


def build_landmark_payload():
    points = {
        1: (0.50, 0.48, 0.00),
        6: (0.50, 0.38, 0.00),
        33: (0.40, 0.45, 0.00),
        133: (0.48, 0.45, 0.00),
        144: (0.445, 0.468, 0.00),
        152: (0.50, 0.72, 0.00),
        153: (0.435, 0.468, 0.00),
        158: (0.445, 0.432, 0.00),
        160: (0.435, 0.432, 0.00),
        234: (0.28, 0.50, 0.00),
        263: (0.60, 0.46, 0.00),
        362: (0.52, 0.46, 0.00),
        373: (0.555, 0.478, 0.00),
        380: (0.565, 0.478, 0.00),
        385: (0.565, 0.442, 0.00),
        387: (0.555, 0.442, 0.00),
        454: (0.72, 0.50, 0.00),
        468: (0.442, 0.450, 0.00),
        473: (0.558, 0.460, 0.00),
    }
    return [
        {"id": idx, "x": x, "y": y, "z": z, "pixel_x": int(x * 1000), "pixel_y": int(y * 1000)}
        for idx, (x, y, z) in points.items()
    ]


def build_test_video_bytes():
    with TemporaryDirectory() as temp_dir:
        video_path = Path(temp_dir) / "sample.avi"
        writer = cv2.VideoWriter(
            str(video_path),
            cv2.VideoWriter_fourcc(*"MJPG"),
            5.0,
            (64, 64),
        )
        if not writer.isOpened():
            raise RuntimeError("Could not create test video.")

        for i in range(6):
            frame = np.zeros((64, 64, 3), dtype=np.uint8)
            frame[:, :, 0] = i * 20
            frame[:, :, 1] = 80
            frame[:, :, 2] = 140
            writer.write(frame)

        writer.release()
        return video_path.read_bytes()


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_and_health(self):
        root_response = self.client.get("/")
        self.assertEqual(root_response.status_code, 200)
        self.assertEqual(root_response.json()["docs"], "/docs")

        health_response = self.client.get("/health")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.json(), {"status": "ok"})

    def test_session_lifecycle(self):
        create_response = self.client.post("/api/v1/sessions")
        self.assertEqual(create_response.status_code, 200)
        session_id = create_response.json()["session_id"]
        self.assertTrue(session_id)

        reset_response = self.client.post(f"/api/v1/sessions/{session_id}/reset")
        self.assertEqual(reset_response.status_code, 200)
        self.assertTrue(reset_response.json()["reset"])

        delete_response = self.client.delete(f"/api/v1/sessions/{session_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.json()["deleted"])

    def test_score_endpoint(self):
        payload = {
            "face_count": 1,
            "features": {
                "gaze_x": 0.10,
                "gaze_y": 0.00,
                "blink_rate": 12.0,
                "head_yaw": 3.0,
                "head_pitch": 1.0,
                "head_roll": 0.5,
                "ear": 0.24,
            },
        }
        response = self.client.post("/api/v1/score", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["label"], "NORMAL")
        self.assertEqual(body["score"], 0)

    def test_score_endpoint_flags_multiple_faces(self):
        payload = {
            "face_count": 2,
            "features": {
                "gaze_x": 0.10,
                "gaze_y": 0.00,
                "blink_rate": 12.0,
                "head_yaw": 3.0,
                "head_pitch": 1.0,
                "head_roll": 0.5,
                "ear": 0.24,
            },
        }
        response = self.client.post("/api/v1/score", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["label"], "SUSPICIOUS")
        self.assertGreaterEqual(body["score"], 75)

    def test_analyze_landmarks_endpoint(self):
        create_response = self.client.post("/api/v1/sessions")
        session_id = create_response.json()["session_id"]
        payload = {
            "session_id": session_id,
            "face_count": 1,
            "landmarks": build_landmark_payload(),
        }
        response = self.client.post("/api/v1/analyze/landmarks", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["detected"])
        self.assertEqual(body["session_id"], session_id)
        self.assertIn("gaze_x", body["features"])
        self.assertIn("blink_rate", body["features"])

    def test_invalid_image_returns_400(self):
        response = self.client.post(
            "/api/v1/analyze/image",
            files={"image": ("fake.txt", b"not-an-image", "text/plain")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("valid image", response.json()["detail"])

    def test_video_endpoint_with_valid_video(self):
        try:
            video_bytes = build_test_video_bytes()
        except RuntimeError as exc:
            self.skipTest(str(exc))

        response = self.client.post(
            "/api/v1/analyze/video",
            files={"video": ("sample.avi", video_bytes, "video/x-msvideo")},
            data={
                "sample_every_n_frames": "1",
                "max_frames": "4",
                "include_frame_results": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["filename"], "sample.avi")
        self.assertGreaterEqual(body["frames_processed"], 1)
        self.assertGreaterEqual(body["frames_sampled"], 1)
        self.assertIn("frame_results", body)
        self.assertIn("events", body)
        self.assertIn("alerts", body)
        self.assertIn("suspicious_event_count", body)
        self.assertIn("observations", body["frame_results"][0])

    def test_video_endpoint_can_skip_landmarks(self):
        try:
            video_bytes = build_test_video_bytes()
        except RuntimeError as exc:
            self.skipTest(str(exc))

        response = self.client.post(
            "/api/v1/analyze/video",
            files={"video": ("sample.avi", video_bytes, "video/x-msvideo")},
            data={
                "sample_every_n_frames": "1",
                "max_frames": "2",
                "include_landmarks": "false",
                "include_frame_results": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["frame_results"][0]["landmarks"])

    def test_video_sampling_spreads_across_full_clip(self):
        try:
            video_bytes = build_test_video_bytes()
        except RuntimeError as exc:
            self.skipTest(str(exc))

        response = self.client.post(
            "/api/v1/analyze/video",
            files={"video": ("sample.avi", video_bytes, "video/x-msvideo")},
            data={
                "sample_every_n_frames": "1",
                "max_frames": "2",
                "include_frame_results": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["frames_sampled"], 2)
        self.assertEqual(body["frame_results"][0]["frame_index"], 0)
        self.assertGreaterEqual(body["frame_results"][1]["frame_index"], 5)
        self.assertGreaterEqual(body["frames_processed"], 6)

    def test_video_summary_endpoint_returns_key_frames(self):
        try:
            video_bytes = build_test_video_bytes()
        except RuntimeError as exc:
            self.skipTest(str(exc))

        response = self.client.post(
            "/api/v1/analyze/video/summary",
            files={"video": ("sample.avi", video_bytes, "video/x-msvideo")},
            data={
                "sample_every_n_frames": "1",
                "max_frames": "4",
                "max_key_frames": "3",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["filename"], "sample.avi")
        self.assertIn("events", body)
        self.assertIn("alerts", body)
        self.assertIn("key_frames", body)
        self.assertLessEqual(len(body["key_frames"]), 3)
        self.assertNotIn("frame_results", body)

    def test_invalid_video_returns_400(self):
        response = self.client.post(
            "/api/v1/analyze/video",
            files={"video": ("fake.mp4", b"not-a-video", "video/mp4")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("valid video", response.json()["detail"])

    def test_dataset_endpoints(self):
        list_response = self.client.get("/api/v1/datasets")
        self.assertEqual(list_response.status_code, 200)
        datasets = list_response.json()
        self.assertGreaterEqual(len(datasets), 1)

        filename = datasets[0]["name"]
        download_response = self.client.get(f"/api/v1/datasets/{filename}")
        self.assertEqual(download_response.status_code, 200)
        self.assertIn("timestamp", download_response.text)

    def test_dataset_path_traversal_is_blocked(self):
        response = self.client.get("/api/v1/datasets/../secrets.txt")
        self.assertEqual(response.status_code, 404)

    def test_transient_no_face_events_are_filtered(self):
        service = AnalysisService()
        frame_results = [
            {
                "frame_index": 0,
                "timestamp_seconds": 0.0,
                "sample_window_seconds": 0.9,
                "label": "NO_FACE",
                "score": None,
                "signals": [
                    {
                        "code": "no_face",
                        "severity": "high",
                        "message": "No face detected in this sampled frame.",
                    }
                ],
            },
            {
                "frame_index": 30,
                "timestamp_seconds": 1.0,
                "sample_window_seconds": 0.9,
                "label": "NORMAL",
                "score": 0,
                "signals": [],
            },
        ]
        events = service._build_events(frame_results)
        event_codes = [event["signal_code"] for event in events]
        self.assertNotIn("no_face", event_codes)

    def test_risk_score_not_created_when_specific_signal_exists(self):
        service = AnalysisService()
        frame_results = [
            {
                "frame_index": 0,
                "timestamp_seconds": 0.0,
                "sample_window_seconds": 1.0,
                "label": "CAUTION",
                "score": 45,
                "signals": [
                    {
                        "code": "head_turn_left",
                        "severity": "high",
                        "message": "Head turned toward the left.",
                        "value": -20.0,
                    }
                ],
            },
            {
                "frame_index": 20,
                "timestamp_seconds": 1.0,
                "sample_window_seconds": 1.0,
                "label": "NORMAL",
                "score": 0,
                "signals": [],
            },
        ]
        events = service._build_events(frame_results)
        event_codes = [event["signal_code"] for event in events]
        self.assertIn("head_turn_left", event_codes)
        self.assertNotIn("risk_score", event_codes)


if __name__ == "__main__":
    unittest.main()
