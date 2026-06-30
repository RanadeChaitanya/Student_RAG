# Studob â€” Progress Summary

## Goal
Build a complete, working MVP of an AI-powered adaptive tutoring platform for JEE students, including a web frontend.

## Approach
- No external AI API dependency (mock LLM layer for MVP)
- Deterministic, testable components
- Modular architecture with interface-first design
- Configuration-driven (YAML + env override)
- SQLite for zero-setup persistence, FAISS for vector storage

---

## Project Structure

```
studob/
â”œâ”€â”€ analytics/          # Mastery trends, mistake patterns, session reports
â”œâ”€â”€ api/                # FastAPI routes, middleware, static frontend
â”‚   â”œâ”€â”€ routes/         # 8 route modules (students, questions, sessions, etc.)
â”‚   â””â”€â”€ static/         # Single-page HTML/JS dashboard
â”œâ”€â”€ assessment/         # Answer evaluator, tagger, assessment engine
â”œâ”€â”€ config/             # Pydantic Settings + YAML loader
â”œâ”€â”€ database/           # SQLAlchemy ORM models, async engine
â”œâ”€â”€ diagnosis/          # Error type registry, root cause classifier, engine
â”œâ”€â”€ embeddings/         # Deterministic hash-based generator, FAISS storage
â”œâ”€â”€ graph/              # In-memory concept graph (66 nodes, 72 edges)
â”œâ”€â”€ llm/                # LLM client ABC, mock client, practice generators
â”œâ”€â”€ question_bank/      # App & test question services, metadata filter
â”œâ”€â”€ retrieval/          # Hybrid pipeline (semantic, metadata, concept, reranking)
â”œâ”€â”€ schemas/            # Pydantic schemas (student, question, session, etc.)
â”œâ”€â”€ student/            # Profile, mastery (Bayesian-like), session memory
â”‚
tests/
â”œâ”€â”€ unit/               # 53 tests across 8 modules
â”œâ”€â”€ integration/        # 1 full workflow test (API-level, 10 steps)
â”‚
scripts/
â”œâ”€â”€ seed_data.py        # Seeds DB + FAISS index with sample data
â”œâ”€â”€ test_api.py         # Standalone end-to-end API test
â”œâ”€â”€ test_faiss.py       # FAISS index validation
â”œâ”€â”€ create_dirs.ps1     # Directory scaffolding
â”‚
configs/development/    # YAML config with all tunable parameters
data/                   # SQLite DB, FAISS index, concept graph JSON
docs/                   # Engineering decisions, this summary
```

---

## What's Implemented

### Foundation Layer
- Config loader: Pydantic Settings + YAML + env override (`SURAJ_ENV`)
- Structured JSON logging via stdlib logging
- 11 custom exception classes
- Async SQLAlchemy engine with session factory
- 9 ORM models: Student, MasteryScore, AppQuestion, TestQuestion, Attempt, Session, MistakeRecord, ConceptNode, Misconception
- 8 Pydantic schema modules with full Field descriptions

### Student Model
- `StudentProfileService`: CRUD + `get_student_by_name`
- `MasteryService`: Bayesian-like mastery update, weak topic identification
- `SessionMemoryService`: session lifecycle, attempt recording

### Question Bank
- `AppQuestionService`, `TestQuestionService` (fully separated)
- `MetadataFilterService`: dynamic SQLAlchemy filtering

### Concept Graph
- In-memory graph store with BFS traversal
- Prerequisite chain discovery, path finding
- JSON-loaded from `data/concept_graph.json` (66 nodes, 72 edges)

### Embeddings
- Deterministic hash-based embedding generator (fixed-dimension)
- FAISS `IndexIDMap` with `IndexFlatIP`
- Save/load cycle for persistence

### Mistake Diagnosis
- `ErrorTypeRegistry`: 7 error categories with patterns + remediation strategies
- Rule-based `RootCauseClassifier` (response time, hints, mastery, recurrence)
- `DiagnosisEngine`: context loading, persistence, history, pattern analysis

### Hybrid Retrieval Pipeline
13-step pipeline: MetadataFilter â†’ SemanticRetrieval â†’ ConceptExpansion â†’ StudentFilter â†’ MistakePatternMatcher â†’ CrossEncoderReranker â†’ ContextBuilder

### LLM Layer
- `LlmClient` ABC with `MockLlmClient` (templated JSON responses)
- `PracticeGenerator` ABC with `MockPracticeGenerator` (orders by difficulty)
- `LlmPracticeGenerator` (prompt rendering + LLM call, ready for real LLM)

### Assessment Engine
- MC exact match, numerical tolerance evaluation
- Concept metadata tagging
- Full assessment lifecycle: create, submit, complete, get

### Analytics
- `MasteryTrendService`, `MistakePatternService`, `SessionReportService`
- Aggregated `StudentAnalyticsResponse`

### API Layer (FastAPI)
- 8 route modules: students, questions, sessions, diagnosis, retrieval, practice, assessment, analytics
- Middleware: logging + error handling
- Dependency injection via `AppContext`, lifespan-managed initialization
- 10/10 endpoints passing

### Frontend
- Single-page HTML/JS dashboard served at `/`
- Student selector, mastery summary, Diagnose/Practice/Analytics buttons
- Tabbed JSON output panel with syntax-colored responses
- Zero build step, no external CDN dependencies

---

## Testing & Quality

| Metric | Result |
|---|---|
| Unit tests | 53 passing |
| Integration tests | 1 passing (10-step workflow) |
| Ruff linting | 0 errors |
| Ruff formatting | Applied across 54 files |

---

## Configuration (`configs/development/config.yaml`)

All tunable parameters live here:
- Mastery thresholds (pass/fail decay, weak topic cutoff)
- Retrieval top-K values (semantic, metadata, final)
- Reranker weights (recency, difficulty, concept match)
- LLM settings (model, temperature, max tokens)
- Assessment settings (passing score, numerical tolerance)
- Diagnosis thresholds (time, hints, recurrence)

---

## How to Run

```powershell
cd D:\JEE\p1
python scripts\seed_data.py   # first time only
python main.py                # starts uvicorn on :8000
```

- Dashboard: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs

---

## Key Decisions (see `docs/engineering_decisions.md` for full details)

- Python 3.11+ / FastAPI / SQLAlchemy + SQLite / FAISS CPU
- Deterministic hash embeddings (no external API needed)
- In-memory concept graph (JSON-loaded)
- Mock LLM layer (templated responses from retrieved questions)
- Module `__init__.py` re-exports only public interfaces
- `pytest` + `pytest-asyncio` with `asyncio_mode="auto"`
- Frontend: minimal HTML/JS served via FastAPI `HTMLResponse`

---

## Next Steps

1. Performance tests for retrieval pipeline and assessment engine
2. Edge case validation (empty question bank, no sessions, concurrent sessions)
3. Integration test for FAISS save/load cycle (cross-restart persistence)
4. Deployment to hosting platform (Render, Railway, cloud VM)
