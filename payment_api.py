
"""Simulated external payment service for incident monitoring."""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# Store logs inside the project.
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "payment_api.log"

# Use UTC timestamps so the incident detector can parse them.
class UTCFormatter(logging.Formatter):
    converter = __import__("time").gmtime


formatter = UTCFormatter(
    fmt="%(asctime)sZ %(levelname)s payment-api %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

logger = logging.getLogger("payment_api")
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(file_handler)
logger.propagate = False

app = FastAPI(
    title="Simulated Payment Service",
    description="A demo API that generates logs for incident monitoring.",
    version="1.0.0",
)


class PaymentRequest(BaseModel):
    amount: float = Field(gt=0, le=1_000_000)
    simulate_failure: bool = False


@app.get("/health")
def health():
    return {"status": "healthy", "service": "payment-api"}


@app.post("/payments")
def create_payment(payment: PaymentRequest):
    request_id = str(uuid.uuid4())

    if payment.simulate_failure:
        logger.error(
            "request failed status=500 route=/payments "
            "request_id=%s reason=simulated_failure amount=%.2f",
            request_id,
            payment.amount,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Simulated payment failure",
                "request_id": request_id,
            },
        )

    logger.info(
        "request completed status=200 route=/payments "
        "request_id=%s amount=%.2f",
        request_id,
        payment.amount,
    )

    return {
        "status": "success",
        "service": "payment-api",
        "request_id": request_id,
        "amount": payment.amount,
    }


@app.post("/demo/failure")
def generate_demo_failure():
    """Generate one intentional error for monitoring tests."""
    request_id = str(uuid.uuid4())

    logger.error(
        "request failed status=500 route=/demo/failure "
        "request_id=%s reason=demo_failure",
        request_id,
    )

    raise HTTPException(
        status_code=500,
        detail={
            "message": "Intentional demo failure",
            "request_id": request_id,
        },
    )
