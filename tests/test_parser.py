import pandas as pd
import pytest
from rpa_analyzer.parser import normalize_logs

def test_normalize_logs_maps_status_and_optional_fields():
    source = pd.DataFrame({
        "Start Time": ["2026-01-01T10:00:00Z", "2026-01-01T10:05:00Z"],
        "Workflow": ["InvoiceBot", "InvoiceBot"],
        "Job State": ["Successful", "Faulted"],
        "Error": ["", "BusinessRuleException"],
        "Seconds": [30, 12],
    })
    result = normalize_logs(source, {
        "timestamp": "Start Time", "process_name": "Workflow", "status": "Job State",
        "exception_type": "Error", "duration_seconds": "Seconds",
    }, "UiPath")
    assert list(result["status"]) == ["Succeeded", "Failed"]
    assert result.loc[1, "exception_type"] == "BusinessRuleException"
    assert result.loc[0, "platform"] == "UiPath"

def test_normalize_logs_requires_core_mappings():
    with pytest.raises(ValueError, match="Missing required column mappings"):
        normalize_logs(pd.DataFrame({"Workflow": ["Bot"]}), {"process_name": "Workflow"}, "Automation Anywhere")

def test_normalize_logs_rejects_invalid_timestamp():
    source = pd.DataFrame({"When": ["not-a-date"], "Process": ["Bot"], "Status": ["Completed"]})
    with pytest.raises(ValueError, match="invalid or empty timestamp"):
        normalize_logs(source, {"timestamp": "When", "process_name": "Process", "status": "Status"}, "Automation Anywhere")


def test_normalize_logs_accepts_valid_and_blank_durations():
    source = pd.DataFrame({
        "When": ["2026-01-01T10:00:00Z"] * 4,
        "Process": ["Bot"] * 4,
        "Status": ["Completed"] * 4,
        "Duration": ["30", "0", "12.5", ""],
    })

    result = normalize_logs(
        source,
        {
            "timestamp": "When",
            "process_name": "Process",
            "status": "Status",
            "duration_seconds": "Duration",
        },
        "UiPath",
    )

    assert result["duration_seconds"].iloc[0] == 30
    assert result["duration_seconds"].iloc[1] == 0
    assert result["duration_seconds"].iloc[2] == 12.5
    assert pd.isna(result["duration_seconds"].iloc[3])


@pytest.mark.parametrize("duration", ["abc", "-10", "inf", "-inf", "nan"])
def test_normalize_logs_rejects_invalid_durations(duration):
    source = pd.DataFrame({
        "When": ["2026-01-01T10:00:00Z"],
        "Process": ["Bot"],
        "Status": ["Completed"],
        "Duration": [duration],
    })

    with pytest.raises(ValueError, match="row 2"):
        normalize_logs(
            source,
            {
                "timestamp": "When",
                "process_name": "Process",
                "status": "Status",
                "duration_seconds": "Duration",
            },
            "UiPath",
        )


def test_normalize_logs_reports_multiple_invalid_duration_rows():
    source = pd.DataFrame({
        "When": ["2026-01-01T10:00:00Z"] * 3,
        "Process": ["Bot"] * 3,
        "Status": ["Completed"] * 3,
        "Duration": ["abc", "10", "-5"],
    })

    with pytest.raises(ValueError) as exc_info:
        normalize_logs(
            source,
            {
                "timestamp": "When",
                "process_name": "Process",
                "status": "Status",
                "duration_seconds": "Duration",
            },
            "UiPath",
        )

    assert "row 2" in str(exc_info.value)
    assert "row 4" in str(exc_info.value)
