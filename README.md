# DepTrace

DepTrace is an Enterprise RAG (Retrieval-Augmented Generation) and Dependency Tracing system designed to analyze cross-team discussions, operational issues, and engineering dependency chains.

## Project Structure

```
deptrace/
├── backend/
│   ├── extraction/                   # Semantic extraction foundation (Step 6)
│   │   ├── __init__.py
│   │   ├── schema.py                 # Semantic entity and statement schemas + provenance
│   │   ├── base.py                   # Extractor interfaces and heuristic baseline
│   │   ├── selector.py               # Deterministic message selection utilities
│   │   └── extract_slice.py          # Message slice semantic extraction runner
│   ├── graph/
│   │   ├── README.md                 # HydraDB compatibility & setup guide
│   │   ├── schema.py                 # Canonical graph ontology & query definitions
│   │   ├── test_hydra.py             # HydraDB smoke test and query validation script
│   │   ├── ingest_candidates.py      # Ingests deterministic candidate graph into HydraDB
│   │   └── verify_ingestion.py       # Multi-hop graph traversal verification script
│   └── ingestion/
│       ├── parse_slack.py            # Slack dump parser converting text threads to JSONL
│       ├── validate_slack_parse.py   # Dataset validation and integrity audit
│       └── build_graph_candidates.py # Deterministic structural graph candidate generator
├── tests/
│   ├── test_build_graph_candidates.py # Unit tests for candidate generation
│   ├── test_ingest_candidates.py      # Unit tests for HydraDB candidate ingestion
│   └── test_semantic_extraction.py    # Unit tests for semantic schemas and provenance
├── frontend/                         # DepTrace UI client
├── .gitignore
└── README.md
```

## Features

- **Semantic Extraction Foundation (Step 6)**: Provider-agnostic extraction architecture, structured schemas (`Customer`, `Project`, `Incident`, `Decision`, `ConfigurationChange`, `Statement`), and bidirectional message/document provenance.
- **HydraDB Graph Foundation**: Canonical ontology with standalone `MERGE` write patterns and multi-hop Cypher queries.
- **Deterministic Candidate Ingestion (Step 5B)**: Converts candidate graphs into supported standalone `MERGE` statements with embedded properties and integer IDs into HydraDB.
- **Deterministic Graph Candidate Generation (Step 5A)**: Constructs structural graph elements (`Document`, `Channel`, `Message`, `Person`, `Team`) and relationships (`IN_CHANNEL`, `AUTHORED`, `MEMBER_OF`, `PART_OF`) with stable 63-bit integer IDs.
- **Slack Log Parsing & Normalization (Step 5C)**: Extracts channel metadata, author, team, and multi-line message threads with fenced code block and header validation.

## Getting Started

### Prerequisites

- Python 3.9+
- Docker (for local HydraDB instance)
- `requests` (`pip install requests`)

### HydraDB Graph Setup & Smoke Test

1. Start HydraDB with in-memory storage provider:
   ```bash
   docker run -d --name hydradb \
     -p 8443:8443 \
     -p 7687:7687 \
     -e CLOUD_PROVIDER=memory \
     -e GRAPH_ALLOW_PLAINTEXT=true \
     ghcr.io/hydra-db/hydradb:latest
   ```

2. Set environment variables:
   ```bash
   # PowerShell
   $env:HYDRA_TOKEN = (docker exec hydradb cat /data/auth-token)
   $env:HYDRA_URL = "http://127.0.0.1:8443"

   # Bash
   export HYDRA_TOKEN=$(docker exec hydradb cat /data/auth-token)
   export HYDRA_URL="http://127.0.0.1:8443"
   ```

3. Run smoke test:
   ```bash
   python backend/graph/test_hydra.py
   ```

### Slack Log Ingestion & Candidate Graph Pipeline

1. Parse raw Slack export files into structured JSONL:
   ```bash
   python backend/ingestion/parse_slack.py
   ```

2. Generate deterministic graph candidate records:
   ```bash
   python backend/ingestion/build_graph_candidates.py
   ```

3. Ingest candidate documents into HydraDB (default: initial 10 documents):
   ```bash
   python backend/graph/ingest_candidates.py
   ```

4. Verify multi-hop graph reads in HydraDB:
   ```bash
   python backend/graph/verify_ingestion.py
   ```

### Semantic Extraction (Step 6 Foundation)

Run semantic extraction on a small deterministic slice of messages:

```bash
# Sample from initial documents
python backend/extraction/extract_slice.py --docs 3 --msgs-per-doc 5

# Target specific domain keywords
python backend/extraction/extract_slice.py --keywords "concurrency,rollback,ACME"
```

### Running Tests

```bash
python -m unittest discover tests -v
```
