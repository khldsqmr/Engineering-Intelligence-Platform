
# CodePulse

AI-powered Engineering Intelligence Platform.

## Overview

CodePulse is designed to transform engineering collaboration
data into actionable analytical insights and evidence-based
AI narratives.

The platform uses GitHub as its initial data source.

## Technology Stack

- Backend: Python, FastAPI, Pydantic and HTTPX
- Frontend: React, TypeScript and Vite
- Database: SQLite (planned)
- AI Inference: Ollama (planned)
- Code Quality: Ruff and Oxlint
- Testing: Pytest
- Version Control: Git and GitHub

## Local Development

### Prerequisites

- Python 3.14
- Node.js 24
- npm
- Git

### Backend

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[development]"
python -m uvicorn backend.main:app --reload
```

Backend: http://127.0.0.1:8000

API Documentation: http://127.0.0.1:8000/docs

### Frontend

In a separate terminal:

```bash
cd frontend
npm ci
npm run dev
```

Frontend: http://127.0.0.1:5173

## Quality Checks

### Backend

```bash
python -m ruff check backend
python -m ruff format --check backend
python -m pytest -v
```

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

## Project Status

The initial full-stack application foundation is implemented.
GitHub ingestion, analytical processing and AI-generated
insights are under development.
