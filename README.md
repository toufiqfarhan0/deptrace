# Veridex (DeTrace) — Hackathon Track 1

**Evidence-first dependency intelligence and grounded investigation console over HydraDB.**

Veridex investigates incidents, operational changes, and cross-team dependencies across unstructured enterprise communications. By leveraging **HydraDB** as a deterministic semantic knowledge graph and provenance layer, Veridex resolves typed facts, actions, and decisions without hallucinated linkages.

---

## Veridex Architecture

```
                    EnterpriseRAG-Bench Dataset
                                │
                                ▼
                   Deterministic Slack Parser
                                │
                                ▼
                       HydraDB Graph Layer
            ┌───────────────────┴───────────────────┐
            ▼                                       ▼
    Semantic Entities & Statements           Source Provenance
 (MENTIONS, EXPRESSES, ABOUT)             (message_id, document_id)
            └───────────────────┬───────────────────┘
                                │
                                ▼
                 Deterministic Graph Retriever
                                │
                                ▼
                     Evidence Bundle [E1, E2]
                                │
                                ▼
                   Grounded Gemini Graph RAG
                                │
                                ▼
                    Evidence-Backed Synthesis
                                │
                                ▼
                Multi-Hop Dependency Tracer (BFS)
                                │
                                ▼
               Veridex Investigation Console (React)
```

---

## Why HydraDB is Essential to Veridex

Veridex does **not** treat the database as simple vector storage or passive context caching:

1. **Deterministic Graph Resolution**: Rather than asking an LLM to search or guess relationships, HydraDB resolves typed statements (`fact`, `action`, `decision`, `outcome`, `claim`) and direct `(Statement)-[:ABOUT]->(Entity)` edges deterministically via OpenCypher queries.
2. **Bounded Evidence Packaging**: Retrieval constructs discrete, stable evidence items `[E1], [E2], ...` mapped to explicit graph nodes and relationships.
3. **Strict Grounded Synthesis**: Gemini operates strictly on the deterministic evidence bundle, citing bracketed evidence tags `[E1, E2]` for every factual assertion.
4. **Zero-Hallucination Dependency Tracing**: Multi-hop BFS tracing explores real graph edges with cycle protection and bounded depth. If teams, authors, or channels are not present in the graph, Veridex explicitly reports *"Not available in current graph"* instead of hallucinating links.
5. **Verifiable Provenance Invariants**: Every evidence item, dependency hop, and chronological timeline event preserves immutable source message and document IDs.

---

## 3–5 Minute Hackathon Demo Flow

### Narrative: "What happened with REL-311?"

1. **Launch Investigation**: Enter `"What happened with REL-311?"` in the Veridex Query Console.
2. **Deterministic Retrieval**: HydraDB queries find relevant `ABOUT` edges and typed statements across the graph slice in **<80ms**.
3. **Provenance-Preserved Evidence**: Evidence items `[E1]`, `[E2]` display exact statement type badges (`FACT`, `ACTION`), graph relationships (`ABOUT`), and source provenance (`msg:8537794879600693670`).
4. **Grounded Synthesis**: Gemini synthesizes the answer citing `[E1, E2]`. Citation pills are interactive—clicking `[E1]` scrolls and highlights the underlying evidence row.
5. **Grounding Verification**: The console verifies citations against retrieved IDs and displays `GROUNDED · Evidence-backed synthesis`.
6. **Multi-Hop Dependency Trace**: Switch to the **Trace** tab for `REL-311` (depth=2). HydraDB traverses the graph:
   ```
   REL-311 ⟷ api-search ⟷ v3.1.1-legacy-tokenizer ⟷ v3.1.1-legacy-tokenizer pinned to 1%
   ```
7. **Chronological Timeline**: View the exact ordered timeline of actions (`01 [fact] Monitor snapshot in eu-west`, `02 [action] Variant test rollout`, `03 [fact] Release notes and support alert link`).
8. **Live Evaluation & Invariants**: Open **Why HydraDB?** to execute the live benchmark and verify 100% provenance integrity across all graph items.

---

## Project Structure

```
deptrace/
├── backend/
│   ├── semantic/                     # Semantic schema, extraction & HydraDB ingestion (Step 6)
│   │   ├── schema.py                 # Semantic entity, statement & extraction models (Pydantic)
│   │   ├── ingest_semantic.py        # Ingests semantic pilot results into HydraDB (MERGE patterns)
│   │   ├── verify_semantic_graph.py  # Graph query helper & validation routines
│   │   └── ids.py                    # Deterministic 63-bit integer ID generator (MurmurHash3)
│   ├── retrieval/                    # Deterministic retrieval & dependency tracing (Step 7, Step 11)
│   │   ├── hydra_retriever.py        # OpenCypher graph snapshot queries & evidence ranking
│   │   ├── dependency_tracer.py      # Multi-hop BFS dependency tracer & timeline generator
│   │   ├── models.py                 # Retrieval & Trace Pydantic data contracts
│   │   └── verify_trace.py           # Dependency tracing verification script
│   ├── rag/                          # Grounded Graph RAG & Citation Validation (Step 8, Step 10)
│   │   ├── answer_generator.py       # Google GenAI SDK Gemini Interactions API generator
│   │   ├── rag_pipeline.py           # Citation parsing [E1, E2] & grounding verifier
│   │   └── models.py                 # RAG query and response models
│   ├── evaluation/                   # Hackathon Evaluation, Provenance & Ablation (Step 12)
│   │   ├── evaluation_runner.py      # Benchmark runner, invariant verifier & ablation engine
│   │   ├── models.py                 # Evaluation report & invariant data models
│   │   └── verify_evaluation.py      # Standalone evaluation & ablation validation script
│   └── api/                          # FastAPI REST Application (Step 9)
│       ├── app.py                    # FastAPI application factory & React SPA server
│       ├── routes.py                 # Endpoints (/api/health, /api/ask, /api/trace, /api/evaluation)
│       └── verify_api.py             # API endpoint verification script
├── frontend-react/                   # Veridex Investigation Console (React 19 + Vite 6)
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx           # Technical navigation sidebar & HydraDB telemetry
│   │   │   ├── InvestigationView.jsx # Terminal query console & dense evidence rows
│   │   │   ├── TraceView.jsx         # Multi-hop path visualizer & statement timeline
│   │   │   ├── EntityExplorer.jsx    # Graph entity catalog with filterable search
│   │   │   ├── GraphHealth.jsx       # Real-time HydraDB connection health & API catalog
│   │   │   └── WhyHydraDB.jsx        # Architecture principles & live ablation benchmark
│   │   ├── index.css                 # Technical console design system (Amber / JetBrains Mono)
│   │   └── App.jsx                   # Main application workspace shell
├── tests/                            # Comprehensive offline pytest suite (133 tests)
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- Docker (for local HydraDB instance)
- Google Gemini API key (optional for UI review; all tests and evaluations run offline)

### 1. Start Local HydraDB Instance

```bash
docker run -d --name hydradb \
  -p 8443:8443 \
  -p 7687:7687 \
  -e CLOUD_PROVIDER=memory \
  -e GRAPH_ALLOW_PLAINTEXT=true \
  ghcr.io/hydra-db/hydradb:latest
```

Set environment variables:
```bash
# PowerShell
$env:HYDRA_TOKEN = (docker exec hydradb cat /data/auth-token)
$env:HYDRA_URL = "http://127.0.0.1:8443"

# Linux / macOS
export HYDRA_TOKEN=$(docker exec hydradb cat /data/auth-token)
export HYDRA_URL="http://127.0.0.1:8443"
```

### 2. Ingest Semantic Knowledge Graph Slice

```bash
python -m backend.semantic.ingest_semantic
```

### 3. Build Frontend & Start Veridex Console

```bash
# Build React application
npm run build --prefix frontend-react

# Start FastAPI backend
uvicorn backend.api.app:app --reload --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## Verification & Testing Commands

All unit tests and benchmark suites execute **100% offline** without consuming Gemini API quota:

```bash
# 1. Run full offline unit test suite (133 tests)
python -m pytest -q

# 2. Run Step 12 Evaluation, Provenance Invariant Check, & Ablation Benchmark
python -m backend.evaluation.verify_evaluation

# 3. Run Step 11 Dependency Tracing Verification
python -m backend.retrieval.verify_trace

# 4. Run Step 9 Web API Verification
python -m backend.api.verify_api

# 5. Build React production bundle
npm run build --prefix frontend-react
```
