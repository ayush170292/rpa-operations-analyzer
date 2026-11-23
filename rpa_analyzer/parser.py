import math

import pandas as pd

REQUIRED_FIELDS = [
    ("timestamp", "Execution start or event time", True),
    ("process_name", "Process, workflow or automation name", True),
    ("status", "Execution status or state", True),
    ("exception_type", "Exception or error category", False),
    ("exception_message", "Exception or error details", False),
    ("duration_seconds", "Execution duration in seconds", False),
    ("robot", "Robot, machine or runner name", False),
    ("job_id", "Unique job or execution identifier", False),
]

CANONICAL_COLUMNS = [
    "platform", "timestamp", "process_name", "status", "exception_type",
    "exception_message", "duration_seconds", "robot", "job_id"
]


def _normalize_status(value):
    text = str(value).strip().lower()
    if text in {"success", "successful", "succeeded", "completed", "complete", "passed"}:
        return "Succeeded"
    if text in {"fail", "failed", "failure", "error", "faulted", "aborted"}:
        return "Failed"
    if text in {"running", "in progress", "pending", "queued", "started"}:
        return "Running"
    return "Other"


def _validate_durations(values):
    raw_values = values.fillna("").astype(str).str.strip()
    numeric_values = pd.to_numeric(
        raw_values.replace("", pd.NA),
        errors="coerce"
    )

    invalid = []
    for position, (raw, numeric) in enumerate(
        zip(raw_values, numeric_values)
    ):
        if raw == "":
            continue

        if pd.isna(numeric):
            reason = "not a valid number"
        elif not math.isfinite(float(numeric)):
            reason = "must be a finite number"
        elif numeric < 0:
            reason = "cannot be negative"
        else:
            continue

        csv_row = position + 2
        invalid.append(f"row {csv_row} ({raw!r}: {reason})")

    if invalid:
        raise ValueError(
            "Invalid execution duration(s): " + "; ".join(invalid)
        )

    return numeric_values


def normalize_logs(frame, column_mapping, platform):
    """Map a platform CSV into the common execution-log schema."""
    required = {"timestamp", "process_name", "status"}
    missing = required - set(column_mapping)
    if missing:
        raise ValueError(
            "Missing required column mappings: " + ", ".join(sorted(missing))
        )

    absent = set(column_mapping.values()) - set(frame.columns)
    if absent:
        raise ValueError(
            "Mapped columns are not present in the uploaded CSV: "
            + ", ".join(sorted(absent))
        )

    result = pd.DataFrame(index=frame.index)
    result["platform"] = platform

    for field in CANONICAL_COLUMNS:
        if field == "platform":
            continue
        source = column_mapping.get(field)
        result[field] = frame[source] if source else ""

    result["timestamp"] = pd.to_datetime(
        result["timestamp"], errors="coerce", utc=True
    )
    result["process_name"] = (
        result["process_name"].fillna("").astype(str).str.strip()
    )
    result["status"] = result["status"].map(_normalize_status)

    for field in ["exception_type", "exception_message", "robot", "job_id"]:
        result[field] = (
            result[field].fillna("").astype(str).str.strip()
        )

    result["duration_seconds"] = _validate_durations(
        result["duration_seconds"]
    )

    if result["timestamp"].isna().any():
        raise ValueError(
            f"{int(result['timestamp'].isna().sum())} "
            "row(s) have an invalid or empty timestamp."
        )

    if result["process_name"].eq("").any():
        raise ValueError(
            f"{int(result['process_name'].eq('').sum())} "
            "row(s) have an empty process name."
        )

    return result[CANONICAL_COLUMNS].reset_index(drop=True)
