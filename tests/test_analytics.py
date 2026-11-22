import pandas as pd
from rpa_analyzer.analytics import build_summary, top_exceptions

def test_build_summary_counts_statuses_and_success_rate():
    frame = pd.DataFrame({"status": ["Succeeded", "Succeeded", "Failed", "Running", "Other"]})
    assert build_summary(frame) == {
        "total": 5, "succeeded": 2, "failed": 1, "running": 1, "other": 1, "success_rate": 40.0
    }

def test_top_exceptions_groups_failed_rows_only():
    frame = pd.DataFrame({
        "status": ["Failed", "Failed", "Succeeded"],
        "exception_type": ["Timeout", "Timeout", "None"],
    })
    assert top_exceptions(frame).to_dict("records") == [{"Exception type": "Timeout", "Occurrences": 2}]
