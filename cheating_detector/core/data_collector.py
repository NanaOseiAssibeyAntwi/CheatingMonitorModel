import csv
import time
from datetime import datetime
from pathlib import Path

from cheating_detector.settings import DATASET_DIR


class DataCollector:
    """
    Saves one row per second to a CSV file for model training.

    CSV columns:
        timestamp, gaze_x, gaze_y, blink_rate,
        head_yaw, head_pitch, head_roll,
        mouth_mar, mouth_movement, speech_activity, is_speaking,
        label
    """

    CSV_COLUMNS = [
        "timestamp",
        "gaze_x",
        "gaze_y",
        "blink_rate",
        "head_yaw",
        "head_pitch",
        "head_roll",
        "mouth_mar",
        "mouth_movement",
        "speech_activity",
        "is_speaking",
        "label",
    ]

    def __init__(self, output_dir: str | Path | None = None):
        output_path = Path(output_dir) if output_dir else DATASET_DIR
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filepath = output_path / f"session_{timestamp}.csv"
        self._file = self.filepath.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.CSV_COLUMNS)
        self._writer.writeheader()
        self._last_write = time.time()
        self._current_label = 0
        self._rows_written = 0
        print(f"[DataCollector] Saving to {self.filepath}")

    def set_label(self, label: int):
        """Call with 0 (normal) or 1 (suspicious) when the operator presses a key."""
        self._current_label = label
        print(
            f"[DataCollector] Label set -> {'NORMAL' if label == 0 else 'SUSPICIOUS'}"
        )

    def try_write(self, features: dict, elapsed: float):
        """
        Writes a row approximately once per second.
        elapsed : seconds since session start.
        """
        now = time.time()
        if now - self._last_write >= 1.0:
            row = {
                "timestamp": round(elapsed, 1),
                "gaze_x": features["gaze_x"],
                "gaze_y": features["gaze_y"],
                "blink_rate": features["blink_rate"],
                "head_yaw": features["head_yaw"],
                "head_pitch": features["head_pitch"],
                "head_roll": features["head_roll"],
                "mouth_mar": features.get("mouth_mar", 0.0),
                "mouth_movement": features.get("mouth_movement", 0.0),
                "speech_activity": features.get("speech_activity", 0.0),
                "is_speaking": int(bool(features.get("is_speaking", False))),
                "label": self._current_label,
            }
            self._writer.writerow(row)
            self._last_write = now
            self._rows_written += 1

    def close(self):
        self._file.close()
        print(
            f"[DataCollector] Session saved - {self._rows_written} rows -> {self.filepath}"
        )
