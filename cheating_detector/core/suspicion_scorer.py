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
    GAZE_Y_THRESHOLD = 0.35
    YAW_THRESHOLD = 15.0
    PITCH_THRESHOLD = 12.0
    ROLL_THRESHOLD = 16.0
    BLINK_LOW = 5.0
    BLINK_HIGH = 30.0
    SPEECH_ACTIVITY_THRESHOLD = 0.45

    def __init__(self):
        self._history = deque(maxlen=self.WINDOW_SIZE)

    def _rule_based_score(self, features):
        """Returns a raw [0, 1] suspicion value for this single frame."""
        score = 0.0
        if abs(features.get("gaze_x", 0.0)) > self.GAZE_X_THRESHOLD:
            score += 0.30
        if abs(features.get("gaze_y", 0.0)) > self.GAZE_Y_THRESHOLD:
            score += 0.20
        if abs(features.get("head_yaw", 0.0)) > self.YAW_THRESHOLD:
            score += 0.25
        if abs(features.get("head_pitch", 0.0)) > self.PITCH_THRESHOLD:
            score += 0.15
        if abs(features.get("head_roll", 0.0)) > self.ROLL_THRESHOLD:
            score += 0.10
        speech_activity = features.get("speech_activity")
        if speech_activity is not None and speech_activity > self.SPEECH_ACTIVITY_THRESHOLD:
            score += 0.10
        blink_rate = features.get("blink_rate", 0.0)
        if blink_rate > 0 and (blink_rate < self.BLINK_LOW or blink_rate > self.BLINK_HIGH):
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
