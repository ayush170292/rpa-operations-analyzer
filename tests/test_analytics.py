import pandas as pd
import pytest
from rpa_analyzer.analytics import build_summary, top_exceptions
from rpa_analyzer.analytics import build_process_summary

from datetime import date
from rpa_analyzer.analytics import filter_execution_logs



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



def test_build_process_summary_calculates_process_metrics():
    frame = pd.DataFrame({
        "process_name": ["InvoiceBot", "InvoiceBot", "InvoiceBot", "HRBot"],
        "status": ["Succeeded", "Succeeded", "Failed", "Failed"],
        "duration_seconds": [10.0, 20.0, 30.0, 40.0],
    })

    result = build_process_summary(frame)

    invoice = result[result["Process"] == "InvoiceBot"].iloc[0]
    assert invoice["Executions"] == 3
    assert invoice["Succeeded"] == 2
    assert invoice["Failed"] == 1
    assert invoice["Success rate"] == pytest.approx(66.6667, rel=1e-4)
    assert invoice["Average duration (seconds)"] == 20.0


def test_build_process_summary_handles_empty_input():
    frame = pd.DataFrame({
        "process_name": [],
        "status": [],
        "duration_seconds": [],
    })

    result = build_process_summary(frame)

    assert result.empty
    assert "Process" in result.columns

def test_build_daily_trends_calculates_daily_execution_metrics():
    from rpa_analyzer.analytics import build_daily_trends

    frame = pd.DataFrame({
        "timestamp": [
            "2026-01-01T08:00:00Z",
            "2026-01-01T09:00:00Z",
            "2026-01-01T10:00:00Z",
            "2026-01-02T08:00:00Z",
        ],
        "status": ["Succeeded", "Succeeded", "Failed", "Failed"],
    })

    result = build_daily_trends(frame)

    assert len(result) == 2

    first_day = result.iloc[0]
    assert str(first_day["Date"]) == "2026-01-01"
    assert first_day["Total executions"] == 3
    assert first_day["Succeeded"] == 2
    assert first_day["Failed"] == 1
    assert first_day["Success rate"] == pytest.approx(66.6667, rel=1e-4)


def test_build_daily_trends_handles_empty_input():
    from rpa_analyzer.analytics import build_daily_trends

    frame = pd.DataFrame({
        "timestamp": [],
        "status": [],
    })

    result = build_daily_trends(frame)

    assert result.empty
    assert "Date" in result.columns




def test_filter_execution_logs_by_process():
    frame = pd.DataFrame({
        "process_name": ["InvoiceBot", "HRBot", "InvoiceBot"],
        "status": ["Succeeded", "Failed", "Failed"],
        "timestamp": pd.to_datetime([
            "2026-01-01T08:00:00Z",
            "2026-01-01T09:00:00Z",
            "2026-01-02T08:00:00Z",
        ]),
    })

    result = filter_execution_logs(
        frame,
        processes=["InvoiceBot"],
    )

    assert len(result) == 2
    assert result["process_name"].eq("InvoiceBot").all()


def test_filter_execution_logs_by_status():
    frame = pd.DataFrame({
        "process_name": ["InvoiceBot", "HRBot", "PaymentBot"],
        "status": ["Succeeded", "Failed", "Succeeded"],
        "timestamp": pd.to_datetime([
            "2026-01-01T08:00:00Z",
            "2026-01-01T09:00:00Z",
            "2026-01-02T08:00:00Z",
        ]),
    })

    result = filter_execution_logs(frame, statuses=["Failed"])

    assert len(result) == 1
    assert result.iloc[0]["status"] == "Failed"


def test_filter_execution_logs_by_date_range():
    frame = pd.DataFrame({
        "process_name": ["Bot"] * 3,
        "status": ["Succeeded"] * 3,
        "timestamp": pd.to_datetime([
            "2026-01-01T08:00:00Z",
            "2026-01-02T08:00:00Z",
            "2026-01-03T08:00:00Z",
        ]),
    })

    result = filter_execution_logs(
        frame,
        start_date=date(2026, 1, 2),
        end_date=date(2026, 1, 3),
    )

    assert len(result) == 2


def test_filter_execution_logs_combines_all_filters():
    frame = pd.DataFrame({
        "process_name": ["InvoiceBot", "InvoiceBot", "HRBot"],
        "status": ["Succeeded", "Failed", "Failed"],
        "timestamp": pd.to_datetime([
            "2026-01-01T08:00:00Z",
            "2026-01-02T08:00:00Z",
            "2026-01-02T09:00:00Z",
        ]),
    })

    result = filter_execution_logs(
        frame,
        processes=["InvoiceBot"],
        statuses=["Failed"],
        start_date=date(2026, 1, 2),
        end_date=date(2026, 1, 2),
    )

    assert len(result) == 1
    assert result.iloc[0]["process_name"] == "InvoiceBot"
    assert result.iloc[0]["status"] == "Failed"


def test_filter_execution_logs_returns_empty_result_when_no_match():
    frame = pd.DataFrame({
        "process_name": ["InvoiceBot"],
        "status": ["Succeeded"],
        "timestamp": pd.to_datetime(["2026-01-01T08:00:00Z"]),
    })

    result = filter_execution_logs(
        frame,
        processes=["HRBot"],
    )

    assert result.empty
