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
