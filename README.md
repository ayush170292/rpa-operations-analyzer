# RPA Operations Analyzer

A lightweight Streamlit dashboard for analyzing CSV execution logs from UiPath and Automation Anywhere.

## Features
- Upload execution logs as CSV.
- Select UiPath or Automation Anywhere as the source platform.
- Map platform-specific columns to a common schema.
- Normalize common execution states into Succeeded, Failed, Running and Other.
- Review execution totals, success rate and recurring exception types.
- Download normalized execution records as CSV.

## Format note
RPA products and versions can export different CSV layouts. This starter does not claim to parse every native export automatically. Configurable column mapping adapts different export headers.

## Setup
Python 3.10+ is required.

```bash
python -m venv .venv
```

Windows activation:
```powershell
.venv\Scripts\activate
```

macOS/Linux activation:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run dashboard:
```bash
streamlit run app.py
```

Upload `sample_data/sample_execution_logs.csv`. Map Timestamp to Start Time, Process name to Workflow, Status to Job State, and optionally map the remaining fields.

Run tests from the project root:
```bash
pytest -q
```

## Canonical fields
`platform`, `timestamp`, `process_name`, `status`, `exception_type`, `exception_message`, `duration_seconds`, `robot`, `job_id`.

## Current limitations
CSV input only; no direct platform APIs, Excel input, database, authentication or multi-user storage. Duration is expected in seconds when mapped.
