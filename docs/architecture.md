# Studob Architecture

## System Overview

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Browser   â”‚â”€â”€â”€â”€â–¶â”‚  FastAPI     â”‚â”€â”€â”€â”€â–¶â”‚  SQLite      â”‚
â”‚  (SPA SPA)  â”‚â—€â”€â”€â”€â”€â”‚  (Uvicorn)   â”‚â—€â”€â”€â”€â”€â”‚  (aiosqlite) â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                           â”‚
                           â–¼
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚  FAISS       â”‚     â”‚  Concept     â”‚
                    â”‚  Vector DB   â”‚     â”‚  Graph       â”‚
                    â”‚  (in-memory) â”‚     â”‚  (JSON)      â”‚
                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Vector Database (FAISS)

### What is FAISS?
FAISS (Facebook AI Similarity Search) is a library for efficient similarity search and clustering of dense vectors. In Studob, it serves as our vector database â€” storing embeddings of all practice questions and retrieving the most relevant ones for a given query.

### How it Works

#### 1. Embedding Generation
Each question in the bank is converted into a vector (embedding) that represents its semantic meaning:

```
Question text â”€â”€â–¶ EmbeddingGenerator â”€â”€â–¶ 384-dim vector
     â”‚                                        â”‚
     â”‚                                        â–¼
  "What is the   â”€â”€â–¶  Hash-based       â”€â”€â–¶  [0.23, -0.45,
   derivative         deterministic          0.67, ... 384 values]
   of xÂ²?"           embedding
```

**Current approach**: We use a deterministic hash-based embedding (`studob/embeddings/generator.py`). This is an MVP choice â€” it creates reproducible embeddings from question text using hashing + normalization, producing 384-dimensional vectors. This avoids needing an external embedding API.

#### 2. Indexing
After generating embeddings, they are stored in a FAISS `IndexFlatIP` (Inner Product / cosine similarity):

```
All question embeddings â”€â”€â–¶ FAISS IndexFlatIP â”€â”€â–¶ data/faiss_index.bin
```

- **Index type**: `IndexFlatIP` â€” brute-force inner product search. For MVP with 20-100 questions, this is fast enough. For production with millions, we'd use `IndexIVFFlat` (inverted file indexing).
- **Persistence**: The index is saved to disk as `data/faiss_index.bin` with metadata in `data/faiss_index.bin.meta`.
- **Loading**: On app startup, `VectorStoreService.load()` reads the index and metadata into memory.

#### 3. Retrieval
When a query comes in (e.g., "find questions about Newton's laws"):

```
Query: "Newton's laws"
    â”‚
    â–¼
EmbeddingGenerator.generate("Newton's laws")
    â”‚
    â–¼
[0.12, 0.89, -0.34, ...]
    â”‚
    â–¼
FAISS Index.search(query_vector, k=5)
    â”‚
    â–¼
Returns: [question_id_3, question_id_7, question_id_12, ...]
         (sorted by similarity score)
```

### Why Not a Full Vector DB (Pinecone, Weaviate, etc.)?
- **MVP simplicity**: FAISS in-memory requires zero infrastructure
- **Deterministic**: Hash embeddings are reproducible across runs
- **Speed**: Sub-millisecond queries for our data size
- **No API costs**: No external service dependency

### Future Upgrade Path
```
FAISS (MVP) â”€â”€â–¶ pgvector (PostgreSQL) â”€â”€â–¶ Pinecone/Weaviate (Production)
  Flat index       + B-tree filtering       + Distributed search
  In-memory        + Disk-based             + High availability
  < 100K vectors   < 1M vectors             > 1M vectors
```

---

## Embedding Strategy

### Hash-Based (Current)
```python
# Simplified from studob/embeddings/generator.py
def generate(text: str) -> list[float]:
    # Deterministic hash of text segments
    # Produces same vector for same input every time
    # Dimension: 384 (matches popular embedding models)
    return normalized_hash_vector(text)
```

**Pros**: Zero external dependencies, deterministic, fast
**Cons**: No semantic understanding â€” "car" and "automobile" map to different vectors

### Future: Real Embeddings
```python
# Planned for production
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode(question_text)  # True semantic embedding
```

---

## Concept Graph

### What is it?
A directed graph of 66 JEE concepts with 72 prerequisite relationships, stored as `data/concept_graph.json`.

### Structure
```json
{
  "nodes": [
    {"id": "calculus", "subject": "mathematics", "topic": "calculus",
     "difficulty": 2, "description": "..."},
    {"id": "differentiation", "subject": "mathematics", "topic": "calculus",
     "difficulty": 3, "description": "..."},
    ...
  ],
  "edges": [
    {"source": "calculus", "target": "differentiation",
     "relationship": "prerequisite"},
    {"source": "differentiation", "target": "integration",
     "relationship": "prerequisite"},
    ...
  ],
  "misconceptions": [...]
}
```

### Usage
- **Prerequisite chain discovery**: "To learn Integration, you need Differentiation first, which needs Calculus"
- **Weak topic root cause**: "You struggled with Electrostatics because your grasp of Electric Fields is weak"
- **Adaptive practice selection**: Pick questions from prerequisite concepts when a student struggles

---

## Hybrid Retrieval Pipeline

The 13-step pipeline in `studob/retrieval/orchestrator.py`:

```
Student Query
    â”‚
    â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 1. MetadataFilterService                â”‚
â”‚    Filter by subject/topic/difficulty    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                 â”‚
                 â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 2. SemanticSearch (FAISS vector DB)     â”‚
â”‚    Find semantically similar questions  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                 â”‚
                 â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 3. ConceptExpansion                     â”‚
â”‚    Add related concept questions        â”‚
â”‚    (from concept graph BFS)             â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                 â”‚
                 â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 4. StudentFilter                        â”‚
â”‚    Exclude already-mastered topics      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                 â”‚
                 â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 5. MistakeMatcher                       â”‚
â”‚    Prioritize questions matching past   â”‚
â”‚    mistake categories                   â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                 â”‚
                 â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 6. Reranker                             â”‚
â”‚    Re-rank by:                          â”‚
â”‚    - Difficulty match to student level  â”‚
â”‚    - Concept graph distance             â”‚
â”‚    - Mistake recency                    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                 â”‚
                 â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ 7. ContextBuilder                       â”‚
â”‚    Assemble final context with:         â”‚
â”‚    - Retrieved questions                â”‚
â”‚    - Relevant concept paths             â”‚
â”‚    - Mistake history summary            â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

Each step is **configurable via feature flags** in `config.yaml`, allowing individual steps to be enabled/disabled for testing.

---

## Mistake Diagnosis Engine

### Error Categories (7 types)
| Category | Example | Detection |
|---|---|---|
| `concept_misunderstood` | Applied wrong formula | Answer doesn't match any known wrong pattern |
| `formula_recall_failure` | Knew concept, forgot formula | Similar questions correct, this one formula-dependent |
| `calculation_error` | Arithmetic mistake | Answer close to correct, off by factor |
| `sign_unit_error` | Wrong sign/unit | Answer matches correct magnitude but sign mismatch |
| `misread_question` | Answered what was NOT asked | Answer matches a plausible but different question interpretation |
| `guessing` | Random answer | Answer doesn't correspond to any option pattern |
| `careless` | Lost focus | Previously correct on similar, now wrong |

### Root Cause Classification
Uses decision tree + student history to classify each mistake:

```python
class RootCauseClassifier:
    def classify(question, student_answer, student_history):
        if is_calculation_error(student_answer, question):
            return "calculation_error"
        if is_sign_error(student_answer, question):
            return "sign_unit_error"
        # ... more rules
        return classifier.predict(features)
```

---

## Data Flow: End-to-End

### Practice Session
```
1. User clicks "Start Practice"
2. POST /api/v1/practice/generate
3. Orchestrator builds query from:
   - Student's weak topics (from MasteryService)
   - Error category (from DiagnosisEngine)
   - Question count
4. HybridRetrievalPipeline retrieves questions
5. Session created in DB with UUID
6. Questions displayed in frontend
7. User answers â†’ Attempt stored in DB
8. POST /api/v1/practice/{id}/result
9. MasteryService.update_mastery() â†’ updates scores
10. DiagnosisEngine records mistakes
```

### Assessment Flow
```
1. POST /api/v1/assessment/ â†’ creates session
2. GET /api/v1/assessment/{id} â†’ get questions
3. POST /api/v1/assessment/{id}/answer â†’ submit per-question
4. POST /api/v1/assessment/{id}/complete â†’ finalize
5. AnswerEvaluator scs â†’ AnswerTagger tags concepts
6. AssessmentResult returned with topic breakdown
```

---

## Directory Structure

```
studob/
â”œâ”€â”€ api/
â”‚   â”œâ”€â”€ routes/          # FastAPI routers (8 modules)
â”‚   â”‚   â”œâ”€â”€ students.py
â”‚   â”‚   â”œâ”€â”€ questions.py
â”‚   â”‚   â”œâ”€â”€ sessions.py
â”‚   â”‚   â”œâ”€â”€ practice.py
â”‚   â”‚   â”œâ”€â”€ assessment.py
â”‚   â”‚   â”œâ”€â”€ diagnosis.py
â”‚   â”‚   â”œâ”€â”€ analytics.py
â”‚   â”‚   â””â”€â”€ retrieval.py
â”‚   â”œâ”€â”€ static/          # Frontend SPA
â”‚   â”‚   â”œâ”€â”€ index.html
â”‚   â”‚   â”œâ”€â”€ css/style.css
â”‚   â”‚   â””â”€â”€ js/
â”‚   â”‚       â”œâ”€â”€ api.js
â”‚   â”‚       â””â”€â”€ app.js
â”‚   â”œâ”€â”€ app.py           # FastAPI app.factory
â”‚   â”œâ”€â”€ dependencies.py  # AppContext DI
â”‚   â””â”€â”€ middleware.py    # Logging, Auth, Error handlers
â”œâ”€â”€ assessment/          # Assessment engine
â”œâ”€â”€ config/              # Settings, yaml loader
â”œâ”€â”€ database/            # SQLAlchemy ORM models
â”œâ”€â”€ diagnosis/           # Mistake Diagnosis Engine
â”œâ”€â”€ embeddings/          # Vector generation + FAISS
â”œâ”€â”€ llm/                 # LLM abstraction layer (mock)
â”œâ”€â”€ logging_setup.py
â”œâ”€â”€ question_bank/       # Question CRUD + search
â”œâ”€â”€ retrieval/           # Hybrid retrieval pipeline
â”œâ”€â”€ schemas/             # Pydantic models
â””â”€â”€ student/             # Profile, Mastery, Session memory
```

---

## Key Design Decisions

1. **FAISS in-memory**: Zero infra, fast for MVP. Swap for pgvector later.
2. **Hash embeddings**: Deterministic, no API cost. Swap for Sentence Transformers later.
3. **Mock LLM layer**: Templates from retrieved questions. Swap for GPT/Claude via LlmClient ABC.
4. **SQLite + aiosqlite**: Single file, async, zero config. Swap for PostgreSQL later.
5. **UUID session IDs**: Avoids integer ID collisions, works across distributed systems.
6. **Signal-aware mastery**: Confidence increases on correct, decreases on wrong â€” prevents over-confidence.
7. **Lumina Academic dark theme**: Professional dark UI with glassmorphism, 4px grid, Hanken Grotesk.
