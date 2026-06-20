import math
import time


class FeatureExtractor:
    """
    Computes all six FYPGuard features from a MediaPipe landmark list.

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

    EAR_THRESHOLD = 0.20
    BLINK_COOLDOWN = 0.15

    def __init__(self):
        self._blink_count = 0
        self._session_start = time.time()
        self._last_blink_time = 0.0
        self._eye_was_closed = False

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

    def compute_gaze(self, lm):
        """
        Returns (gaze_x, gaze_y) each in [-1, +1].
        Requires iris landmarks (refine_landmarks=True).
        """
        if self.LEFT_IRIS not in lm or self.RIGHT_IRIS not in lm:
            return 0.0, 0.0

        left_iris = lm[self.LEFT_IRIS]
        left_eye_l = lm[self.LEFT_EYE[0]]
        left_eye_r = lm[self.LEFT_EYE[3]]
        eye_width = abs(left_eye_r["x"] - left_eye_l["x"])

        if eye_width == 0:
            gaze_x = 0.0
        else:
            raw_x = (left_iris["x"] - left_eye_l["x"]) / eye_width - 0.5
            gaze_x = max(-1.0, min(1.0, raw_x * 2.0))

        upper_avg_y = (lm[self.LEFT_EYE[1]]["y"] + lm[self.LEFT_EYE[2]]["y"]) / 2
        lower_avg_y = (lm[self.LEFT_EYE[4]]["y"] + lm[self.LEFT_EYE[5]]["y"]) / 2
        eye_height = abs(lower_avg_y - upper_avg_y)

        if eye_height == 0:
            gaze_y = 0.0
        else:
            raw_y = (left_iris["y"] - upper_avg_y) / eye_height - 0.5
            gaze_y = max(-1.0, min(1.0, raw_y * 2.0))

        return round(gaze_x, 4), round(gaze_y, 4)

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

        return round(yaw, 2), round(pitch, 2), round(roll, 2)

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

        return {
            "gaze_x": gaze_x,
            "gaze_y": gaze_y,
            "blink_rate": blink_rate,
            "head_yaw": yaw,
            "head_pitch": pitch,
            "head_roll": roll,
            "ear": round(avg_ear, 4),
        }
