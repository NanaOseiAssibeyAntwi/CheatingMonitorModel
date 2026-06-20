from collections import deque


class SuspicionScorer:
    """
    Rule-based suspicion scorer for use during data collection and
    prototyping - before the TFLite classifier is trained.

    After training, replace _rule_based_score() with a call to your
    TFLite model's output.
    """

    WINDOW_SIZE = 30

    GAZE_X_THRESHOLD = 0.35
    GAZE_Y_THRESHOLD = 0.40
    YAW_THRESHOLD = 20.0
    PITCH_THRESHOLD = 25.0
    BLINK_LOW = 5.0
    BLINK_HIGH = 30.0

    def __init__(self):
        self._history = deque(maxlen=self.WINDOW_SIZE)

    def _rule_based_score(self, features):
        """Returns a raw [0, 1] suspicion value for this single frame."""
        score = 0.0
        if abs(features["gaze_x"]) > self.GAZE_X_THRESHOLD:
            score += 0.30
        if abs(features["gaze_y"]) > self.GAZE_Y_THRESHOLD:
            score += 0.20
        if abs(features["head_yaw"]) > self.YAW_THRESHOLD:
            score += 0.25
        if abs(features["head_pitch"]) > self.PITCH_THRESHOLD:
            score += 0.15
        blink_rate = features["blink_rate"]
        if blink_rate < self.BLINK_LOW or blink_rate > self.BLINK_HIGH:
            score += 0.10
        return min(score, 1.0)

    def update(self, features, classifier_output=None, confidence=1.0):
        """
        classifier_output : 0 or 1 from the TFLite model (or None -> rule-based)
        confidence        : model confidence (0.0 - 1.0)
        Returns rolling average score 0-100 and colour label.
        """
        if classifier_output is not None:
            raw = classifier_output * confidence
        else:
            raw = self._rule_based_score(features)

        self._history.append(raw * 100)
        rolling = sum(self._history) / len(self._history)
        score = round(rolling)

        if score <= 30:
            label, colour = "NORMAL", (0, 200, 0)
        elif score <= 60:
            label, colour = "CAUTION", (0, 165, 255)
        else:
            label, colour = "SUSPICIOUS", (0, 0, 220)

        return score, label, colour
