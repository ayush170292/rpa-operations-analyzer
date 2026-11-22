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
