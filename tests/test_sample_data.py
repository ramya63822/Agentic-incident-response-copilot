from incident_copilot.sample_data import load_sample_log


def test_sample_log_is_available():
    text = load_sample_log()
    assert "payment-api" in text
    assert "ERROR" in text
