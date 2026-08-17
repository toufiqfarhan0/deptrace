# Veridex — Enterprise Knowledge Investigation

**Evidence-first dependency intelligence powered by HydraDB.**

Veridex reconstructs what your engineering organization knows by combining signals from Slack, Linear, and GitHub through a deterministic HydraDB knowledge graph. Every answer is grounded in provenance-tracked evidence. Every dependency is traced, not approximated.

> **HydraDB handles the graph reasoning. Gemini handles the language synthesis.**

This distinction is the core architectural principle of Veridex.

---

## What Veridex Is

Veridex is an enterprise knowledge investigation system built for the **HydraDB Hackathon Track 1: Enterprise Context + Ontology**.

It solves a real problem: enterprise knowledge is fragmented across Slack conversations, Linear issues, and GitHub pull requests. No single system has the full picture. Veridex reconstructs that picture by ingesting signals from all three sources into a unified HydraDB knowledge graph, then provides:

- **Grounded investigation** — ask questions, get evidence-backed answers with citations
- **Dependency tracing** — trace multi-hop relationships between technical entities
- **Provenance verification** — every evidence item retains its source identity
- **Cross-source discovery** — find connections spanning Slack threads, Linear issues, and GitHub PRs

---

## Why HydraDB Is Central

Traditional RAG systems use vector similarity to approximate retrieval. This creates a fundamental problem: approximate retrieval produces approximate facts, which leads to hallucinated linkages in answers.

Veridex uses HydraDB's **deterministic OpenCypher graph traversal** instead:

1. Raw enterprise signals are ingested as a structural + semantic graph
2. When a query arrives, HydraDB traverses graph relationships deterministically
3. Only provenance-grounded evidence is returned — no approximation
4. Gemini synthesizes language only from that bounded evidence bundle

This means Veridex cannot hallucinate a relationship that does not exist in the graph. The architecture structurally prevents it.

---

## Architecture

```
   Slack ──┐
  Linear ──┼──► Canonical Records ──► HydraDB Graph
  GitHub ──┘            │                    │
                        │           ┌─────────────────────┐
              Semantic Extraction   │  Structural Layer   │
              (Gemini, offline OK)  │  - Message          │
                        │           │  - Issue            │
                        ▼           │  - PullRequest      │
              SemanticExtraction   │  - Channel          │
              Entity / Statement   │  - Project          │
              ABOUT relationships  │  - Repository       │
                                   │  - Person / Entity  │
                                   └──────────┬──────────┘
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                    Deterministic      Dependency        Provenance
                    Graph Retrieval    Tracing (BFS)     Validation
                              │               │
                              └───────┬───────┘
                                      ▼
                              Evidence Bundle
                             [E1, E2, E3 ...]
                             (message_id + document_id)
                                      │
                                      ▼
                            Gemini Graph RAG Synthesis
                            (bounded to evidence bundle)
                                      │
                                      ▼
                            Grounded Answer + Citations
```

### Graph Ontology

**Structural nodes**: `Message`, `Issue`, `PullRequest`, `Channel`, `Project`, `Repository`, `Person`, `Entity`

**Structural edges**: `[:IN_CHANNEL]`, `[:PART_OF]`, `[:TARGETS]`, `[:AUTHORED]`, `[:MENTIONS]`

**Semantic nodes**: `SemanticExtraction`, `Statement`

**Semantic edges**: `[:HAS_SEMANTIC_EXTRACTION]`, `[:EXPRESSES]`, `[:ABOUT]`

All IDs are deterministic 63-bit integers derived from `stable_id(source, document_id)`. Ingestion is idempotent.

---

## Supported Sources

| Source | Document Type | Graph Vertex | Key Edge |
|:-------|:-------------|:-------------|:---------|
| **Slack** | Conversations | `Message` | `[:IN_CHANNEL]` |
| **Linear** | Issues & tasks | `Issue` | `[:PART_OF]` |
| **GitHub** | Pull requests | `PullRequest` | `[:TARGETS]` |

No other sources are claimed or integrated.

---

## Grounded Graph RAG Flow

1. **Query arrives** at `/api/ask`
2. **Deterministic retrieval**: HydraDB traverses `MENTIONS`, `EXPRESSES`, and `ABOUT` relationships to collect evidence matching the query entities
3. **Evidence bundle assembled**: each item carries `message_id`, `document_id`, `entity`, `statement_type`, and `relationship_type`
4. **Gemini synthesis**: Gemini receives only the evidence bundle — it cannot access or invent facts outside it
5. **Citation grounding**: the response includes `[E1]`, `[E2]` citations linked to specific evidence items
6. **Provenance preserved**: the full message and document identity is carried through to the final response

---

## Dependency Tracing

The `/api/trace` endpoint performs multi-hop BFS traversal across the HydraDB semantic graph:

```
REL-311
  └─► api-search          (hop 1, msg 8537794879600693670)
  └─► v3.1.1-legacy-tokenizer   (hop 1, msg 8537794879600693670)
      └─► v3.1.1-legacy-tokenizer pinned to 1%  (hop 2)
```

Each hop returns:
- The related entity
- The source message
- The statement type (fact / action / decision / outcome / claim)
- The provenance (message ID, document ID)

---

## Evidence & Provenance

Every evidence item in Veridex retains:

| Field | Description |
|:------|:------------|
| `message_id` | Original HydraDB vertex ID |
| `document_id` | Source document identifier (`dsid_<hex>`) |
| `source` | `slack`, `linear`, or `github` |
| `source_id` | Thread ID, issue key, or PR number |
| `entity` | The matched entity name |
| `statement` | The grounded statement text |
| `statement_type` | `fact`, `action`, `decision`, `outcome`, or `claim` |
| `relationship` | `MENTIONS`, `EXPRESSES`, or `ABOUT` |

Provenance is never discarded. It flows from ingestion through retrieval through synthesis.

---

## Evaluation System

Veridex includes a deterministic evaluation benchmark (`/api/evaluate`) based on 6 reference queries:

- Each query is evaluated against live HydraDB retrieval
- Evidence validity is checked for message IDs and document IDs
- Pass/fail is computed from actual retrieval results — no hardcoded assertions

Current benchmark results (live HydraDB):
- **6/6 queries passed**
- **120/120 evidence items valid**
- **0 missing message IDs**
- **0 provenance errors**

---

## Current Dataset Status

Veridex uses a **controlled 60-document multi-source slice** from the EnterpriseRAG-Bench dataset:

| Source | Documents |
|:-------|:---------:|
| Slack | 20 |
| Linear | 20 |
| GitHub | 20 |
| **Total** | **60** |

**The full EnterpriseRAG-Bench dataset (15,000 documents) is not ingested.**

The repository intentionally uses a controlled slice for the hackathon demo. Dataset files are Git-ignored and must not be committed.

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (for HydraDB)
- HydraDB running locally at `http://127.0.0.1:8443`

### Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI backend (serves the React frontend at /)
uvicorn backend.api.main:app --reload

# Frontend development server (optional)
npm install --prefix frontend-react
npm run dev --prefix frontend-react

# Run all tests (146 tests, fully offline)
python -m pytest -q
```

### Verification Scripts

```bash
# Verify semantic graph integrity
python -m backend.semantic.verify_semantic_graph

# Verify deterministic retrieval
python -m backend.retrieval.verify_retrieval

# Verify dependency tracing
python -m backend.retrieval.verify_trace

# Verify API endpoints
python -m backend.api.verify_api

# Verify 60-document ingestion and provenance
python -m backend.ingestion.verify_multisource_ingestion
```

---

## Demo Walkthrough

### 1. Landing Page
Open the root URL `/`. You will see the Veridex product entry experience explaining the architecture and product story.

### 2. Investigation Console
Click **OPEN INVESTIGATION CONSOLE**. Try:
- `"What happened with REL-311?"`
- `"Why did the team change the model routing?"`
- `"What is the kernel-fallback policy?"`

Each answer will show evidence items `[E1]`, `[E2]` etc. Click a citation to highlight the source evidence.

### 3. Dependency Trace
Navigate to **Trace** and enter `REL-311`. The trace view shows the multi-hop dependency graph and reconstructed timeline.

### 4. Entity Explorer
Navigate to **Entities** to browse all entities in the graph. Click any entity to immediately trace its dependencies.

### 5. Why HydraDB
Navigate to **Why HydraDB?** for the full architecture explanation and evaluation benchmark results.

---

## Project Structure

```
deptrace/
├── backend/
│   ├── api/               # FastAPI routes and web API
│   ├── evaluation/        # Deterministic evaluation benchmark
│   ├── extraction/        # Semantic extraction pipeline
│   ├── graph/             # HydraDB graph utilities
│   ├── ingestion/
│   │   ├── adapters/      # Slack, Linear, GitHub adapters
│   │   ├── canonical.py   # CanonicalRecord Pydantic model
│   │   ├── references.py  # Deterministic reference extractor
│   │   └── writer.py      # HydraDB MERGE query writer
│   ├── rag/               # Grounded Graph RAG pipeline
│   ├── retrieval/         # Deterministic retrieval + trace
│   └── semantic/          # Semantic graph verifiers
├── frontend-react/        # React 19 + Vite 6 frontend
│   └── src/
│       ├── components/
│       │   ├── LandingPage.jsx     # Product entry experience
│       │   ├── InvestigationView.jsx
│       │   ├── TraceView.jsx
│       │   ├── EntityExplorer.jsx
│       │   ├── WhyHydraDB.jsx
│       │   └── GraphHealth.jsx
│       └── App.jsx
├── tests/                 # 146 pytest unit tests
├── data/
│   └── enterprise-rag/    # Git-ignored — not committed
└── README.md
```

---

---

## Deploy to Render (Production Cloud Mode)

Veridex is architected for seamless zero-downtime deployment on **Render** (Free Web Service) with **HydraDB Cloud v2** as the managed production database.

### 1. Architecture on Render
FastAPI serves both the unified REST API (`/api/*`) and the pre-built React 19 single-page application from `frontend-react/dist`. No Node/Vite server is needed in production.

### 2. Required Render Web Service Settings
- **Environment**: `Python 3.11`
- **Build Command**:
  ```bash
  npm install --prefix frontend-react && npm run build --prefix frontend-react && pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn backend.api.app:app --host 0.0.0.0 --port $PORT
  ```
- **Health Check Path**: `/api/health`

### 3. Required Environment Variables

| Variable | Recommended Value | Purpose |
|:---|:---|:---|
| `HYDRA_MODE` | `cloud` | Activates the HydraDB Cloud v2 driver |
| `HYDRA_DB_DATABASE` | `veridex-hackhydra` | Target Cloud database containing the frozen 60-document dataset |
| `HYDRA_DB_BASE_URL` | `https://api.hydradb.com` | HydraDB Cloud v2 API endpoint |
| `HYDRA_DB_API_KEY` | *Secret Token* | Server-side Bearer authentication for HydraDB Cloud |
| `GEMINI_API_KEY` | *Secret Key* | Gemini Interactions API key for grounded synthesis |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Language synthesis model |
| `PYTHON_VERSION` | `3.11.9` | Runtime version |
| `NODE_VERSION` | `20.12.0` | Frontend build version |

> [!WARNING]
> **Security & Zero-Ingestion Rules:**
> - `HYDRA_DB_API_KEY` and `GEMINI_API_KEY` are server-side secrets. They must NEVER be exposed in frontend code or repository commits.
> - The production HydraDB Cloud database `veridex-hackhydra` already contains the complete frozen 60-document dataset. **DO NOT perform any ingestion during deployment or server startup.**

### 4. Local vs. Production Driver Mode
- **Local (`HYDRA_MODE=local`)**: Queries the local Dockerized OpenCypher instance (`:8443`). Used by default for development and offline CI tests.
- **Production (`HYDRA_MODE=cloud`)**: Queries HydraDB Cloud v2 with hybrid retrieval, thinking mode, and forceful relation bindings.
