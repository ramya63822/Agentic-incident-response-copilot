"""Load small, safe sample data bundled with the project."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_sample_log() -> str:
    path = PROJECT_ROOT / "data" / "logs" / "sample_payment.log"
    return path.read_text(encoding="utf-8")
