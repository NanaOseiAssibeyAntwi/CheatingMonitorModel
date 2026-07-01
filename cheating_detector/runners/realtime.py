import time

import cv2

from cheating_detector.core.data_collector import DataCollector
from cheating_detector.core.face_mesh_renderer import FaceMeshRenderer
from cheating_detector.core.feature_extractor import FeatureExtractor
from cheating_detector.core.hud import draw_hud
from cheating_detector.core.suspicion_scorer import SuspicionScorer


def main(collect_mode=False):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return

    renderer = FaceMeshRenderer(max_num_faces=2)
    extractor = FeatureExtractor(auto_calibrate=True, calibration_frames=45)
    scorer = SuspicionScorer()
    collector = DataCollector() if collect_mode else None

    p_time = time.time()
    session_start = time.time()
    features = None
    score, label, colour = 0, "NORMAL", (0, 200, 0)

    print("FYPGuard running. Press Q to quit" + (" and save dataset." if collect_mode else "."))

    while True:
        success, frame = cap.read()
        if not success:
            print("Camera read failed.")
            break

        frame = cv2.flip(frame, 1)

        frame = renderer.find_face(frame, draw=True)
        landmarks = renderer.find_landmarks(frame, draw=False)

        if landmarks:
            features = extractor.extract(landmarks)

        if features:
            if extractor.is_calibrating:
                score, label, colour = 0, "CALIBRATING", (0, 165, 255)
            else:
                score, label, colour = scorer.update(features)

        if renderer.face_count > 1:
            label = "SUSPICIOUS"
            colour = (0, 0, 220)
            score = max(score, 75)

        if collect_mode and collector and features:
            elapsed = time.time() - session_start
            collector.try_write(features, elapsed)

        c_time = time.time()
        fps = 1.0 / max(c_time - p_time, 1e-6)
        p_time = c_time

        draw_hud(
            frame,
            features,
            score,
            label,
            colour,
            fps,
            renderer.face_count,
            collect_mode=collect_mode,
            current_label=collector._current_label if collector else 0,
            calibration_frames_remaining=extractor.calibration_frames_remaining,
        )

        cv2.namedWindow("FYPGuard", cv2.WINDOW_NORMAL)
        cv2.imshow("FYPGuard", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if collect_mode and collector:
            if key == ord("0"):
                collector.set_label(0)
            elif key == ord("1"):
                collector.set_label(1)

    cap.release()
    cv2.destroyAllWindows()
    renderer.close()
    if collector:
        collector.close()
