import math
import time
from collections import deque


class FeatureExtractor:
    """
    Computes core FYPGuard features from a MediaPipe landmark list.

    Landmark index references (MediaPipe 468-point face mesh + iris):
      Left eye  : 33(left corner), 133(right corner),
                  160, 158 (upper lid), 144, 153 (lower lid)
      Right eye : 362(left corner), 263(right corner),
                  387, 385 (upper lid), 373, 380 (lower lid)
      Left iris : 468 (center)
      Right iris: 473 (center)
      Nose tip  : 1
      Chin      : 152
      Left ear  : 234
      Right ear : 454
      Nose bridge top: 6
      Left eye outer corner (for roll): 33
      Right eye outer corner (for roll): 263
      Upper lip center: 13
      Lower lip center: 14
      Mouth corners: 78 (left), 308 (right)
    """

    LEFT_EYE = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    LEFT_IRIS = 468
    RIGHT_IRIS = 473

    NOSE_TIP = 1
    CHIN = 152
    LEFT_EAR = 234
    RIGHT_EAR = 454
    NOSE_BRIDGE = 6
    UPPER_LIP = 13
    LOWER_LIP = 14
    MOUTH_LEFT = 78
    MOUTH_RIGHT = 308

    EAR_THRESHOLD = 0.20
    BLINK_COOLDOWN = 0.15
    CALIBRATION_OUTLIER_GAZE = 0.75
    CALIBRATION_OUTLIER_YAW = 35.0
    CALIBRATION_OUTLIER_PITCH = 35.0
    CALIBRATION_OUTLIER_ROLL = 25.0
    TALK_WINDOW = 20
    MOUTH_OPEN_THRESHOLD = 0.17
    SPEECH_ACTIVITY_THRESHOLD = 0.45

    def __init__(self, auto_calibrate=False, calibration_frames=45):
        self._blink_count = 0
        self._session_start = time.time()
        self._last_blink_time = 0.0
        self._eye_was_closed = False
        self.auto_calibrate = bool(auto_calibrate)
        self.calibration_frames = max(int(calibration_frames), 0)
        self._calibration_frames_seen = 0
        self._calibration_samples = 0
        self._calibration_offsets = {
            "gaze_x": 0.0,
            "gaze_y": 0.0,
            "head_yaw": 0.0,
            "head_pitch": 0.0,
            "head_roll": 0.0,
        }
        self._mouth_mar_history = deque(maxlen=self.TALK_WINDOW)
        self._prev_mouth_mar = None

    @staticmethod
    def _dist(a, b):
        return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)

    @staticmethod
    def _to_dict(lm_list):
        """lm_list item: [id, cx, cy, norm_x, norm_y, norm_z]."""
        return {
            item[0]: {"x": item[3], "y": item[4], "z": item[5]}
            for item in lm_list
        }

    @staticmethod
    def _clamp(value, low, high):
        return max(low, min(high, value))

    def _compute_ear(self, lm, indices):
        """
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        indices order: [p1, p2, p3, p4, p5, p6]
        """
        p = [lm[i] for i in indices]
        vertical1 = self._dist(p[1], p[5])
        vertical2 = self._dist(p[2], p[4])
        horizontal = self._dist(p[0], p[3])
        if horizontal == 0:
            return 0.0
        return (vertical1 + vertical2) / (2.0 * horizontal)

    def update_blink(self, ear):
        """
        Call once per frame with the current average EAR.
        Returns current blinks-per-minute estimate.
        """
        now = time.time()
        elapsed_minutes = max((now - self._session_start) / 60.0, 1 / 60)

        eye_closed = ear < self.EAR_THRESHOLD
        if eye_closed and not self._eye_was_closed:
            if (now - self._last_blink_time) > self.BLINK_COOLDOWN:
                self._blink_count += 1
                self._last_blink_time = now
        self._eye_was_closed = eye_closed

        return round(self._blink_count / elapsed_minutes, 1)

    def _eye_gaze(self, lm, eye_indices, iris_index):
        iris = lm[iris_index]
        corner_a = lm[eye_indices[0]]
        corner_b = lm[eye_indices[3]]

        eye_left = min(corner_a["x"], corner_b["x"])
        eye_right = max(corner_a["x"], corner_b["x"])
        eye_width = eye_right - eye_left

        if eye_width == 0:
            gaze_x = 0.0
        else:
            raw_x = (iris["x"] - eye_left) / eye_width - 0.5
            gaze_x = self._clamp(raw_x * 2.0, -1.0, 1.0)

        upper_avg_y = (lm[eye_indices[1]]["y"] + lm[eye_indices[2]]["y"]) / 2.0
        lower_avg_y = (lm[eye_indices[4]]["y"] + lm[eye_indices[5]]["y"]) / 2.0
        eye_top = min(upper_avg_y, lower_avg_y)
        eye_bottom = max(upper_avg_y, lower_avg_y)
        eye_height = eye_bottom - eye_top

        if eye_height == 0:
            gaze_y = 0.0
        else:
            raw_y = (iris["y"] - eye_top) / eye_height - 0.5
            gaze_y = self._clamp(raw_y * 2.0, -1.0, 1.0)

        return gaze_x, gaze_y

    def compute_gaze(self, lm):
        """
        Returns (gaze_x, gaze_y) each in [-1, +1].
        Requires iris landmarks (refine_landmarks=True).
        """
        required = [
            self.LEFT_EYE[0],
            self.LEFT_EYE[1],
            self.LEFT_EYE[2],
            self.LEFT_EYE[3],
            self.LEFT_EYE[4],
            self.LEFT_EYE[5],
            self.RIGHT_EYE[0],
            self.RIGHT_EYE[1],
            self.RIGHT_EYE[2],
            self.RIGHT_EYE[3],
            self.RIGHT_EYE[4],
            self.RIGHT_EYE[5],
            self.LEFT_IRIS,
            self.RIGHT_IRIS,
        ]
        if not all(key in lm for key in required):
            return 0.0, 0.0

        left_x, left_y = self._eye_gaze(lm, self.LEFT_EYE, self.LEFT_IRIS)
        right_x, right_y = self._eye_gaze(lm, self.RIGHT_EYE, self.RIGHT_IRIS)
        gaze_x = (left_x + right_x) / 2.0
        gaze_y = (left_y + right_y) / 2.0
        return gaze_x, gaze_y

    def compute_head_pose(self, lm):
        """
        Estimates yaw, pitch, roll in degrees using facial geometry.

        Yaw   (left/right turn)  : nose_tip vs midpoint of ears on X axis
        Pitch (up/down tilt)     : nose_tip vs chin on Y axis, normalised
        Roll  (head lean)        : angle of the line between eye corners
        """
        required = [
            self.NOSE_TIP,
            self.CHIN,
            self.LEFT_EAR,
            self.RIGHT_EAR,
            self.LEFT_EYE[0],
            self.RIGHT_EYE[3],
        ]
        if not all(key in lm for key in required):
            return 0.0, 0.0, 0.0

        nose = lm[self.NOSE_TIP]
        chin = lm[self.CHIN]
        left_ear = lm[self.LEFT_EAR]
        right_ear = lm[self.RIGHT_EAR]
        left_eye = lm[self.LEFT_EYE[0]]
        right_eye = lm[self.RIGHT_EYE[3]]

        ear_mid_x = (left_ear["x"] + right_ear["x"]) / 2.0
        face_width = abs(right_ear["x"] - left_ear["x"])
        if face_width == 0:
            yaw = 0.0
        else:
            yaw = ((nose["x"] - ear_mid_x) / face_width) * 90.0

        face_top = lm[self.NOSE_BRIDGE]["y"]
        face_height = abs(chin["y"] - face_top)
        if face_height == 0:
            pitch = 0.0
        else:
            nose_rel = (nose["y"] - face_top) / face_height
            pitch = (nose_rel - 0.45) * 90.0

        dx = right_eye["x"] - left_eye["x"]
        dy = right_eye["y"] - left_eye["y"]
        roll = math.degrees(math.atan2(dy, dx))

        return yaw, pitch, roll

    def compute_mouth_activity(self, lm):
        required = [self.UPPER_LIP, self.LOWER_LIP, self.MOUTH_LEFT, self.MOUTH_RIGHT]
        if not all(key in lm for key in required):
            return 0.0, 0.0, 0.0, False

        mouth_width = self._dist(lm[self.MOUTH_LEFT], lm[self.MOUTH_RIGHT])
        if mouth_width == 0:
            mar = 0.0
        else:
            mouth_height = self._dist(lm[self.UPPER_LIP], lm[self.LOWER_LIP])
            mar = mouth_height / mouth_width

        if self._prev_mouth_mar is None:
            mouth_movement = 0.0
        else:
            mouth_movement = abs(mar - self._prev_mouth_mar)
        self._prev_mouth_mar = mar

        self._mouth_mar_history.append(mar)
        history = list(self._mouth_mar_history)
        variability = (max(history) - min(history)) if len(history) > 1 else 0.0
        open_ratio = (
            sum(1 for value in history if value >= self.MOUTH_OPEN_THRESHOLD) / len(history)
            if history
            else 0.0
        )

        speech_activity = self._clamp(
            (mouth_movement * 8.0) + (variability * 5.0) + max(0.0, open_ratio - 0.25),
            0.0,
            1.0,
        )
        is_speaking = (
            speech_activity >= self.SPEECH_ACTIVITY_THRESHOLD
            and mar >= (self.MOUTH_OPEN_THRESHOLD * 0.8)
        )
        return mar, mouth_movement, speech_activity, is_speaking

    @property
    def is_calibrating(self):
        return self.auto_calibrate and self._calibration_frames_seen < self.calibration_frames

    @property
    def calibration_frames_remaining(self):
        if not self.auto_calibrate:
            return 0
        return max(self.calibration_frames - self._calibration_frames_seen, 0)

    def _sample_is_calibration_safe(self, gaze_x, gaze_y, yaw, pitch, roll):
        return (
            abs(gaze_x) <= self.CALIBRATION_OUTLIER_GAZE
            and abs(gaze_y) <= self.CALIBRATION_OUTLIER_GAZE
            and abs(yaw) <= self.CALIBRATION_OUTLIER_YAW
            and abs(pitch) <= self.CALIBRATION_OUTLIER_PITCH
            and abs(roll) <= self.CALIBRATION_OUTLIER_ROLL
        )

    def _update_calibration_offsets(self, gaze_x, gaze_y, yaw, pitch, roll):
        if not self.is_calibrating:
            return

        self._calibration_frames_seen += 1
        if not self._sample_is_calibration_safe(gaze_x, gaze_y, yaw, pitch, roll):
            return

        self._calibration_samples += 1
        sample_count = self._calibration_samples

        updates = {
            "gaze_x": gaze_x,
            "gaze_y": gaze_y,
            "head_yaw": yaw,
            "head_pitch": pitch,
            "head_roll": roll,
        }
        for key, value in updates.items():
            previous = self._calibration_offsets[key]
            self._calibration_offsets[key] = previous + (value - previous) / sample_count

    def extract(self, lm_list):
        """
        Main entry point.
        lm_list : output of FaceMeshRenderer.find_landmarks()
        Returns dict with keys matching the CSV/model feature names.
        Returns None if no landmarks are available.
        """
        if not lm_list:
            return None

        lm = self._to_dict(lm_list)

        left_ear = self._compute_ear(lm, self.LEFT_EYE)
        right_ear = self._compute_ear(lm, self.RIGHT_EYE)
        avg_ear = (left_ear + right_ear) / 2.0

        blink_rate = self.update_blink(avg_ear)
        gaze_x, gaze_y = self.compute_gaze(lm)
        yaw, pitch, roll = self.compute_head_pose(lm)
        mouth_mar, mouth_movement, speech_activity, is_speaking = self.compute_mouth_activity(lm)

        if self.auto_calibrate:
            self._update_calibration_offsets(gaze_x, gaze_y, yaw, pitch, roll)
            if self._calibration_samples > 0:
                gaze_x -= self._calibration_offsets["gaze_x"]
                gaze_y -= self._calibration_offsets["gaze_y"]
                yaw -= self._calibration_offsets["head_yaw"]
                pitch -= self._calibration_offsets["head_pitch"]
                roll -= self._calibration_offsets["head_roll"]

        gaze_x = self._clamp(gaze_x, -1.0, 1.0)
        gaze_y = self._clamp(gaze_y, -1.0, 1.0)

        return {
            "gaze_x": round(gaze_x, 4),
            "gaze_y": round(gaze_y, 4),
            "blink_rate": blink_rate,
            "head_yaw": round(yaw, 2),
            "head_pitch": round(pitch, 2),
            "head_roll": round(roll, 2),
            "ear": round(avg_ear, 4),
            "mouth_mar": round(mouth_mar, 4),
            "mouth_movement": round(mouth_movement, 4),
            "speech_activity": round(speech_activity, 4),
            "is_speaking": is_speaking,
        }
