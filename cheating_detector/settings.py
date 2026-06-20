from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Cheating Detector API"
APP_VERSION = "1.0.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"


def get_allowed_origins() -> list[str]:
    raw_value = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if not raw_value:
        return ["*"]
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()] or ["*"]
