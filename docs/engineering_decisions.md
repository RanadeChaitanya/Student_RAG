# Engineering Decisions

## Decision Log for Studob MVP

---

### Decision 1: Python as Primary Language

**Decision:** Use Python 3.11+ for the entire backend.

**Reasoning:** Python is widely adopted in AI/ML ecosystems, has excellent support for async (asyncio), and integrates well with all chosen AI/vector libraries. The team is assumed to be comfortable with Python. Type hints in Python 3.11+ are mature enough for production use.

**Alternatives considered:** TypeScript/Node.js, Go, Rust

**Future replacement strategy:** The modular architecture (FastAPI â†’ services â†’ domain modules) means any language could replace the API layer without affecting domain logic.

---

### Decision 2: FastAPI as Web Framework

**Decision:** Use FastAPI for the HTTP API layer.

**Reasoning:** Modern async support, automatic OpenAPI documentation, Pydantic integration for request/response validation, excellent performance via Starlette. This aligns with the project's emphasis on type safety and clean interfaces.

**Alternatives considered:** Flask (sync only, no native OpenAPI), Django (too opinionated, heavy for API), Starlette (too low-level)

**Future replacement strategy:** The API layer is thin (endpoints â†’ services). Can be replaced without touching business logic.

---

### Decision 3: SQLAlchemy + SQLite for MVP RDBMS

**Decision:** Use SQLAlchemy 2.0+ with SQLite for the MVP database, with a clear path to PostgreSQL.

**Reasoning:** SQLAlchemy provides a consistent ORM API regardless of backend. SQLite requires zero setup for development/MVP and is file-based, making it ideal for rapid iteration. The async SQLAlchemy drivers (aiosqlite) allow async session management.

**Alternatives considered:** PostgreSQL directly (too heavy for MVP iteration), raw SQL (no ORM benefits), SQLModel (too new, less mature)

**Future replacement strategy:** Replace `aiosqlite` with `asyncpg` and adjust connection config. SQLAlchemy abstracts the dialect differences.

---

### Decision 4: FAISS for MVP Vector Storage

**Decision:** Use FAISS (CPU) for vector similarity search during MVP.

**Reasoning:** FAISS is lightweight, file-based, and requires no running server. It supports cosine similarity via normalized vectors and HNSW indexing for fast approximate search. For an MVP with thousands of questions, it is more than adequate.

**Alternatives considered:** ChromaDB (more features but heavier), Pinecone (SaaS, requires network, cost), Qdrant (requires running server), pgvector (requires PostgreSQL)

**Future replacement strategy:** The `VectorStore` abstract interface can have an FAISS implementation replaced by Qdrant/Pinecone/ChromaDB implementations without changing any calling code.

---

### Decision 5: Pydantic for All Schemas

**Decision:** Use Pydantic v2 for all data validation and schema definitions throughout the system.

**Reasoning:** Pydantic is the standard for data validation in Python, integrates natively with FastAPI, supports complex nested models, and provides excellent error messages. Using it consistently across config, API schemas, domain schemas, and DB models (via SQLAlchemy's Pydantic support) ensures type safety at every boundary.

**Alternatives considered:** attrs/dataclasses (no validation), msgspec (less ecosystem), manual validation

**Future replacement strategy:** None needed; Pydantic is the standard.

---

### Decision 6: Pytest as Testing Framework

**Decision:** Use pytest with pytest-asyncio for testing.

**Reasoning:** Pytest is the de facto standard for Python testing. pytest-asyncio enables async test support. Fixtures, parametrization, and plugin ecosystem make it highly productive.

**Alternatives considered:** unittest (verbose, no async support), nose (deprecated)

**Future replacement strategy:** None needed.

---

### Decision 7: Ruff for Linting + Formatting

**Decision:** Use Ruff for both linting and code formatting.

**Reasoning:** Ruff is extremely fast (Rust-based), replaces both Flake8 and Black, and has excellent pyproject.toml integration. Single tool for both linting and formatting reduces complexity.

**Alternatives considered:** Black + Flake8 (slower, two tools), pylint (slow, verbose)

**Future replacement strategy:** None needed.

---

### Decision 8: Mock LLM Layer for MVP

**Decision:** Implement a mock/practice-generator that creates structured practice sessions from retrieved context without requiring a real LLM API key.

**Reasoning:** The MVP must work without external API dependencies. The LLM layer will follow the same interface whether backed by OpenAI, Anthropic, or a template-based generator. The mock generator selects questions from the retrieved pool, orders them by difficulty, and adds templated hints/explanations.

**Alternatives considered:** Requiring an LLM API key (blocks MVP testing), hardcoding responses (inflexible)

**Future replacement strategy:** Replace the mock generator with a real LLM client that implements the same `PracticeGenerator` interface.

---

### Decision 9: In-Memory Concept Graph for MVP

**Decision:** Implement the concept graph as an in-memory adjacency-list structure with JSON loading, rather than requiring a graph database (Neo4j/ArangoDB).

**Reasoning:** The concept graph for JEE has ~200-300 nodes and ~400-600 edges. This fits easily in memory and can be loaded from a simple JSON file. A graph database is unnecessary overhead for the MVP.

**Alternatives considered:** Neo4j (requires server), NetworkX (research-oriented, not async), ArangoDB (complex setup)

**Future replacement strategy:** Wrap the in-memory graph in a `ConceptGraphStore` interface. Replace with a Neo4j/ArangoDB implementation when scale demands it.

---

### Decision 10: Single-File Application Entry Point

**Decision:** Use `main.py` at the project root as the application entry point that starts the FastAPI server and initializes all components.

**Reasoning:** Simplicity for MVP. The entry point imports from each module, wires dependencies, and starts uvicorn. This makes the startup sequence explicit and easy to trace.

**Alternatives considered:** Complex bootstrapping framework, Celery-based workers, separate CLI tool

**Future replacement strategy:** Can be split into a proper boot sequence with lifecycle managers as the system grows.

---

### Decision 11: Per-Module Config Sections

**Decision:** Each module defines its config keys in a section namespaced by the module name (e.g., `mastery.weakness_threshold`, `retrieval.top_k`).

**Reasoning:** This prevents key collisions, makes configs self-documenting (you know which module a key belongs to), and enables per-module config validation. Follows the handbook's principle that "no module reads configuration that belongs to another module."

**Alternatives considered:** Flat config keys, ENV-only config, per-module config files

**Future replacement strategy:** None needed.

---

### Decision 12: Loguru-style Structured Logging via stdlib Logger

**Decision:** Use Python's standard `logging` module with structured JSON formatting, not Loguru or other third-party loggers.

**Reasoning:** The stdlib logging module is available everywhere, well understood, and with a custom `JSONFormatter` it can produce structured logs matching the handbook's schema. Adding a third-party logger dependency for the MVP adds risk without meaningful benefit.

**Alternatives considered:** Loguru (third-party dependency, not stdlib), structlog (excellent but another dependency), picologging (C-based but less ecosystem)

**Future replacement strategy:** Can swap to structlog or Loguru without changing log call sites if structured logging needs become more sophisticated.

---

### Decision 13: Data Directory for Runtime State

**Decision:** Use `data/` directory at the project root for SQLite DB files, FAISS index files, and other runtime data.

**Reasoning:** Standard convention. Keeps runtime state separate from source code. The directory is gitignored. Paths are configurable.

**Alternatives considered:** /var/data, ~/.studob, Docker volumes

**Future replacement strategy:** In production, these would be mapped to Docker volumes or cloud storage, not local files.

---

### Decision 14: No Caching Layer for MVP

**Decision:** Skip Redis/memcached for the MVP. Use in-process caching (dict-based) where needed.

**Reasoning:** For a single-server MVP with <100 concurrent users, in-process caching is sufficient. Adding Redis adds deployment complexity without proportional benefit at this stage.

**Alternatives considered:** Redis, memcached, disk-based cache

**Future replacement strategy:** Replace in-process caches with Redis-backed implementations behind the same `CacheStore` interface.

---

### Decision 15: Module `__init__.py` Exports Pattern

**Decision:** Each module's `__init__.py` re-exports only the public interface classes/functions. Internal helpers are not exported.

**Reasoning:** This enforces the handbook's rule that "implementation details stay private." External modules import from `module_name import PublicClass`, never from `module_name._internal_helper`.

**Alternatives considered:** Import everything (leads to coupling), explicit `__all__` (same effect but manual)

**Future replacement strategy:** None needed.
