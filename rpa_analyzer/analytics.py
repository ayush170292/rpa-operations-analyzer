import pandas as pd

def build_summary(frame):
    counts = frame["status"].value_counts()
    total = int(len(frame))
    succeeded = int(counts.get("Succeeded", 0))
    failed = int(counts.get("Failed", 0))
    running = int(counts.get("Running", 0))
    other = total - succeeded - failed - running
    return {
        "total": total, "succeeded": succeeded, "failed": failed,
        "running": running, "other": other,
        "success_rate": (succeeded / total * 100.0) if total else 0.0,
    }

def top_exceptions(frame, limit=10):
    failures = frame.loc[frame["status"] == "Failed"].copy()
    if failures.empty:
        return pd.DataFrame(columns=["Exception type", "Occurrences"])
    failures["exception_type"] = failures["exception_type"].replace("", "Unspecified")
    return (failures.groupby("exception_type").size().sort_values(ascending=False)
            .head(limit).rename_axis("Exception type")
            .reset_index(name="Occurrences"))

def build_process_summary(frame):
    """Build execution and performance metrics grouped by process."""
    if frame.empty:
        return pd.DataFrame(columns=[
            "Process", "Executions", "Succeeded", "Failed",
            "Success rate", "Average duration (seconds)"
        ])

    grouped = frame.groupby("process_name", dropna=False)

    summary = grouped.agg(
        Executions=("status", "size"),
        Succeeded=("status", lambda values: (values == "Succeeded").sum()),
        Failed=("status", lambda values: (values == "Failed").sum()),
        **{
            "Average duration (seconds)": ("duration_seconds", "mean")
        }
    ).reset_index()

    summary["Success rate"] = (
        summary["Succeeded"] / summary["Executions"] * 100
    )

    summary = summary.rename(columns={"process_name": "Process"})

    return summary[
        [
            "Process",
            "Executions",
            "Succeeded",
            "Failed",
            "Success rate",
            "Average duration (seconds)",
        ]
    ].sort_values("Executions", ascending=False).reset_index(drop=True)

def build_daily_trends(frame):
    """Build daily execution volume and outcome metrics."""
    columns = [
        "Date",
        "Total executions",
        "Succeeded",
        "Failed",
        "Success rate",
    ]

    if frame.empty:
        return pd.DataFrame(columns=columns)

    daily = frame.copy()
    daily["Date"] = pd.to_datetime(
        daily["timestamp"], utc=True, errors="coerce"
    ).dt.date

    daily = daily.dropna(subset=["Date"])

    if daily.empty:
        return pd.DataFrame(columns=columns)

    trends = daily.groupby("Date").agg(
        **{
            "Total executions": ("status", "size"),
            "Succeeded": ("status", lambda values: (values == "Succeeded").sum()),
            "Failed": ("status", lambda values: (values == "Failed").sum()),
        }
    ).reset_index()

    trends["Success rate"] = (
        trends["Succeeded"] / trends["Total executions"] * 100
    )

    return trends[columns].sort_values("Date").reset_index(drop=True)

def filter_execution_logs(
    frame,
    processes=None,
    statuses=None,
    start_date=None,
    end_date=None,
):
    """Filter execution logs by process, status and date range."""
    filtered = frame.copy()

    if processes is not None:
        filtered = filtered[
            filtered["process_name"].isin(processes)
        ]

    if statuses is not None:
        filtered = filtered[
            filtered["status"].isin(statuses)
        ]
    if start_date is not None or end_date is not None:
        record_dates = pd.to_datetime(
            filtered["timestamp"], utc=True, errors="coerce"
        ).dt.date

    if start_date is not None:
        filtered = filtered.loc[record_dates >= start_date]

    if end_date is not None:
        record_dates = pd.to_datetime(
            filtered["timestamp"], utc=True, errors="coerce"
        ).dt.date
        filtered = filtered.loc[record_dates <= end_date]

    return filtered.copy()