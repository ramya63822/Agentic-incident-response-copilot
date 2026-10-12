"""Configuration helpers. Secrets are loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_openai_api_key() -> str | None:
    """Return the API key if configured; do not print or log its value."""
    return os.getenv("OPENAI_API_KEY")
