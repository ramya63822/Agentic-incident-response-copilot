# Agentic Incident Response Copilot

A learning and portfolio project exploring how an AI assistant can support software incident investigation using logs, runbooks, deployment context, and historical incidents.

## Current status

The starter includes:
- Streamlit incident intake UI
- Simple keyword-based log triage
- Fictional sample logs and a sample runbook
- Basic unit tests
- Environment-variable configuration for a future OpenAI integration

The starter does **not** yet perform AI diagnosis, vector retrieval, or agentic tool orchestration. Those are planned milestones.

## Requirements

- Python 3.11 or 3.12
- VS Code (recommended)
- An OpenAI API key only when we implement the LLM integration

## Setup on Windows PowerShell

```powershell
cd incident-response-copilot
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use the Python executable inside the virtual environment directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Run the app

```powershell
python -m streamlit run app.py
```

## Run tests

```powershell
python -m pytest -q
```

## OpenAI key setup (later milestone)

1. Copy `.env.example` to `.env`.
2. Add your API key to `OPENAI_API_KEY`.
3. Never commit `.env` or paste the key into source code.
4. The current starter does not make OpenAI API calls yet.

## Project structure

```text
incident-response-copilot/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── incident_copilot/
│   ├── __init__.py
│   ├── config.py
│   ├── log_parser.py
│   ├── sample_data.py
│   └── schemas.py
├── data/
│   ├── logs/
│   │   └── sample_payment.log
│   ├── runbooks/
│   │   └── payment_service.md
│   └── incidents/
│       └── historical_incidents.json
└── tests/
    ├── test_log_parser.py
    └── test_sample_data.py
```

## Planned milestones

1. Verify this starter runs and tests pass.
2. Improve log parsing and evidence extraction.
3. Add retrieval over runbooks and historical incidents.
4. Add OpenAI-powered structured hypotheses with cited evidence.
5. Add a controlled LangGraph investigation workflow.
6. Evaluate known incidents, unsupported claims, latency, and cost.
7. Polish the interface and package the project with Docker.
