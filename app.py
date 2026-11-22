import pandas as pd
import streamlit as st
from rpa_analyzer.parser import REQUIRED_FIELDS, normalize_logs
from rpa_analyzer.analytics import build_summary, top_exceptions

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
    data = st.session_state["normalized"]
    summary = build_summary(data)
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
        exc = top_exceptions(data)
        if exc.empty:
            st.info("No mapped exception types for failed jobs.")
        else:
            st.dataframe(exc, use_container_width=True, hide_index=True)
    st.markdown("#### Normalized execution records")
    st.dataframe(data, use_container_width=True, hide_index=True)
    st.download_button("Download normalized report (CSV)", data.to_csv(index=False).encode("utf-8"),
                       file_name="rpa_execution_report.csv", mime="text/csv")
