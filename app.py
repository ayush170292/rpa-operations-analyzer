import pandas as pd
import streamlit as st

from rpa_analyzer.parser import REQUIRED_FIELDS, normalize_logs

from rpa_analyzer.analytics import (
    build_summary,
    top_exceptions,
    build_process_summary,
    build_daily_trends,
    filter_execution_logs,
)

st.set_page_config(page_title="RPA Operations Analyzer", page_icon="🤖", layout="wide")
st.title("🤖 RPA Operations Analyzer")
st.caption("Analyze UiPath and Automation Anywhere execution logs.")

with st.sidebar:
    platform = st.selectbox("RPA platform", ["UiPath", "Automation Anywhere"])
    upload = st.file_uploader("Upload execution logs (CSV)", type=["csv"])

if upload is None:
    st.info("Upload a CSV execution log to begin. Try sample_data/sample_execution_logs.csv.")
    st.markdown("This starter version uses configurable column mapping because export formats vary by platform and version.")
    st.stop()

try:
    raw = pd.read_csv(upload)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}")
    st.stop()

if raw.empty:
    st.warning("The uploaded CSV contains no data rows.")
    st.stop()

st.subheader("Map your export columns")
mapping = {}
headers = list(raw.columns)
guesses = {
    "timestamp": ["timestamp", "start time", "started", "created", "date"],
    "process_name": ["process", "workflow", "automation", "bot"],
    "status": ["status", "state", "result"],
    "exception_type": ["exception type", "error type", "exception"],
    "exception_message": ["exception message", "error message", "message", "details"],
    "duration_seconds": ["duration seconds", "duration", "elapsed seconds"],
    "robot": ["robot", "machine", "runner", "device"],
    "job_id": ["job id", "execution id", "run id", "id"],
}
for field, description, required in REQUIRED_FIELDS:
    opts = ["— Not mapped —"] + headers
    guess_index = 0
    for guess in guesses[field]:
        match = next((h for h in headers if guess in str(h).strip().lower()), None)
        if match is not None:
            guess_index = opts.index(match)
            break
    mapping[field] = st.selectbox(
        f"{field.replace('_', ' ').title()}{' *' if required else ''} — {description}",
        opts, index=guess_index, key=f"map_{field}"
    )

if st.button("Analyze execution logs", type="primary"):
    missing = [f for f, _, req in REQUIRED_FIELDS if req and mapping[f] == "— Not mapped —"]
    if missing:
        st.error("Map required fields: " + ", ".join(missing))
    else:
        selected = {k: v for k, v in mapping.items() if v != "— Not mapped —"}
        try:
            st.session_state["normalized"] = normalize_logs(raw, selected, platform)
            st.session_state["platform"] = platform
        except ValueError as exc:
            st.error(str(exc))

if "normalized" in st.session_state:
    data = st.session_state["normalized"].copy()

    st.sidebar.divider()
    st.sidebar.subheader("Dashboard filters")

    # Process filter
    process_options = sorted(data["process_name"].unique().tolist())
    selected_processes = st.sidebar.multiselect(
        "Process name",
        options=process_options,
        default=process_options,
    )

    # Status filter
    status_options = ["Succeeded", "Failed", "Running", "Other"]
    available_statuses = [
        status for status in status_options
        if status in data["status"].unique()
    ]
    selected_statuses = st.sidebar.multiselect(
        "Execution status",
        options=available_statuses,
        default=available_statuses,
    )

    # Date range filter
    min_date = data["timestamp"].min().date()
    max_date = data["timestamp"].max().date()

    selected_dates = st.sidebar.date_input(
        "Execution date range",
        value=(min_date, max_date),
        #min_value=min_date,
        #max_value=max_date,
    )

    # Apply filters
    filtered_data = filter_execution_logs(
    data,
    processes=selected_processes,
    statuses=selected_statuses,
    start_date=selected_dates[0] if len(selected_dates) == 2 else None,
    end_date=selected_dates[1] if len(selected_dates) == 2 else None,
    )

    if filtered_data.empty:
        st.warning("No execution records match the selected filters.")
        st.stop()

    summary = build_summary(filtered_data)
#################################################




    st.divider()
    st.subheader(f"Execution overview — {st.session_state['platform']}")
    cols = st.columns(5)
    for col, label, value in zip(
        cols,
        ["Total", "Succeeded", "Failed", "Running", "Success rate"],
        [summary["total"], summary["succeeded"], summary["failed"], summary["running"], f'{summary["success_rate"]:.1f}%']
    ):
        col.metric(label, value)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Execution status")
        chart = pd.DataFrame({"Status": ["Succeeded", "Failed", "Running", "Other"],
                              "Count": [summary["succeeded"], summary["failed"], summary["running"], summary["other"]]})
        st.bar_chart(chart.set_index("Status"))
    with right:
        st.markdown("#### Most frequent exceptions")
        exc = top_exceptions(filtered_data)
        if exc.empty:
            st.info("No mapped exception types for failed jobs.")
        else:
            st.dataframe(exc, width="stretch", hide_index=True)



    st.markdown("#### Daily execution trends")

    daily_trends = build_daily_trends(filtered_data)

    if daily_trends.empty:
        st.info("No daily execution trends available.")
    else:
        trend_chart = daily_trends.set_index("Date")[
            ["Succeeded", "Failed"]
        ]
        st.line_chart(trend_chart, width="stretch")

        st.dataframe(
            daily_trends,
            width="stretch",
            hide_index=True,
            column_config={
                "Success rate": st.column_config.NumberColumn(
                    "Success rate",
                    format="%.2f%%",
                ),
            },
        )

    st.markdown("#### Process-level performance")
    process_summary = build_process_summary(filtered_data)

    if process_summary.empty:
        st.info("No process-level analytics available.")
    else:
        st.dataframe(
            process_summary,
            width="stretch",
            hide_index=True,
            column_config={
                "Success rate": st.column_config.NumberColumn(
                    "Success rate",
                    format="%.2f%%",
                ),
                "Average duration (seconds)": st.column_config.NumberColumn(
                    "Average duration (seconds)",
                    format="%.2f",
                ),
            },
        )
    st.markdown("#### Normalized execution records")
    st.dataframe(filtered_data, width="stretch", hide_index=True)
    st.download_button("Download normalized report (CSV)", filtered_data.to_csv(index=False).encode("utf-8"),file_name="rpa_filtered_execution_report.csv", mime="text/csv")
