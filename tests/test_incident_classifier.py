
from incident_copilot.incident_classifier import classify_incident


def main():

    test_cases = {
        "Simulated incident": [
            "ERROR payment-api reason=simulated_failure",
            "ERROR payment-api reason=simulated_failure",
        ],

        "Operational candidate": [
            "ERROR payment-api database connection timeout",
            "ERROR payment-api request failed status=500",
        ],

        "Mixed incident": [
            "ERROR payment-api reason=simulated_failure",
            "ERROR payment-api database connection timeout",
        ],

        "Unknown incident": [],
    }

    for name, logs in test_cases.items():
        result = classify_incident(logs)

        print(f"\n{name}")
        print("-" * 40)
        print(result)


if __name__ == "__main__":
    main()
