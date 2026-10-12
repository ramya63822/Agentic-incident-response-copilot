from incident_copilot.log_parser import analyze_log_text


def test_counts_lines_and_error_signals():
    text = """INFO service started
ERROR request failed
WARNING retry scheduled
"""
    result = analyze_log_text(text)

    assert result["total_lines"] == 3
    assert result["error_count"] == 1
    assert result["warning_count"] == 1
    assert "ERROR request failed" in result["matching_lines"]
    assert "WARNING retry scheduled" in result["matching_lines"]


def test_empty_log_returns_zero_counts():
    result = analyze_log_text("")

    assert result["total_lines"] == 0
    assert result["error_count"] == 0
    assert result["warning_count"] == 0
    assert result["matching_lines"] == []
