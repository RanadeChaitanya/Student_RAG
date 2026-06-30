# Studob — Adaptive JEE Preparation Platform

AI-powered adaptive tutoring platform for JEE (Joint Entrance Examination) students. Provides personalized practice, assessments, error diagnosis, analytics, and concept mapping — all with deterministic intelligence (no LLM dependency).

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Seed database
python scripts/seed_full.py

# Start server
python main.py
# → http://127.0.0.1:8000/
```

## Features

- **Adaptive Practice** — Questions selected based on student weak topics and mastery scores
- **Assessments** — Timed tests with per-question feedback and mastery updates
- **Error Diagnosis** — Classifies mistakes (formula, sign, unit, concept, etc.) with remediation
- **Analytics Dashboard** — Weak/strong topics, mastery trends, mistake patterns, recommendations
- **Concept Graph** — Visual knowledge graph with prerequisites, gaps, and learning paths
- **PDF Reports** — Per-test HTML reports with score ring, topic breakdown, recommendations
- **Vector Retrieval** — FAISS-based semantic search for mistake matching and context retrieval

## Project Structure

```
studob/              Main application package
  api/               FastAPI web layer (routes, static frontend)
  analytics/         Analytics & reporting service
  assessment/        Assessment engine (create, answer, complete)
  config/            Settings loader
  content_engine/    Hints, explanations, practice selector
  database/          ORM models and engine
  diagnosis/         Error classification and pattern detection
  embeddings/        FAISS vector generation and search
  graph/             Concept knowledge graph
  question_bank/     App and test question services
  retrieval/         Context retrieval orchestrator
  schemas/           Pydantic request/response models
  student/           Mastery, profile, session memory
tests/               Unit and integration tests (176 total)
scripts/             Seed and test utility scripts
configs/             YAML configuration files
docs/                Architecture and engineering documentation
```

## Testing

```bash
# Unit + integration tests (79)
pytest tests/ -v

# API endpoint tests (97) — requires running server with seeded data
python scripts/test_api_endpoints.py
```

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy (async), Pydantic
- **Database:** SQLite via aiosqlite
- **Vector Search:** FAISS (CPU) with deterministic hash embeddings
- **Frontend:** Vanilla JS SPA, CSS dark theme (Inter font)
- **Infrastructure:** Docker, GitHub Actions CI

## License

MIT
