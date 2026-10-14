
"""Generate simulated payment traffic automatically."""

import json
import time
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "http://127.0.0.1:8000/payments"
INTERVAL_SECONDS = 2


def send_payment(request_number: int) -> None:
    # Five successful requests, followed by three intentional failures.
    position = (request_number - 1) % 8
    simulate_failure = position >= 5

    payload = {
        "amount": 500,
        "simulate_failure": simulate_failure,
    }

    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    try:
        with urlopen(request, timeout=5) as response:
            print(
                f"[{timestamp}] Request #{request_number}: "
                f"SUCCESS (HTTP {response.status})"
            )

    except HTTPError as error:
        print(
            f"[{timestamp}] Request #{request_number}: "
            f"SIMULATED FAILURE (HTTP {error.code})"
        )

    except URLError as error:
        print(f"[{timestamp}] API connection failed: {error.reason}")


if __name__ == "__main__":
    print("Payment traffic simulator started.")
    print("Pattern: 5 successes, then 3 intentional failures.")
    print("Press Ctrl+C to stop.\n")

    request_number = 1

    try:
        while True:
            send_payment(request_number)
            request_number += 1
            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nTraffic simulator stopped.")
