# DepTrace

DepTrace is an Enterprise RAG (Retrieval-Augmented Generation) and Dependency Tracing system designed to analyze cross-team discussions, operational issues, and engineering dependency chains.

## Project Structure

```
deptrace/
├── backend/
│   ├── graph/
│   │   ├── README.md                 # HydraDB compatibility & setup guide
│   │   ├── schema.py                 # Canonical graph ontology & query definitions
│   │   ├── test_hydra.py             # HydraDB smoke test and query validation script
│   │   ├── ingest_candidates.py      # Ingests deterministic candidate graph into HydraDB
│   │   └── verify_ingestion.py       # Multi-hop graph traversal verification script
│   └── ingestion/
│       ├── parse_slack.py            # Slack dump parser converting text threads to JSONL
│       └── build_graph_candidates.py # Deterministic structural graph candidate generator
├── tests/
│   ├── test_build_graph_candidates.py # Unit tests for candidate generation
│   └── test_ingest_candidates.py      # Unit tests for HydraDB candidate ingestion
├── frontend/                         # DepTrace UI client
├── .gitignore
└── README.md
```

## Features

- **HydraDB Graph Foundation**: Canonical ontology (`Person`, `Team`, `Customer`, `Incident`, `ConfigurationChange`, etc.) with standalone `MERGE` write patterns and multi-hop Cypher queries.
- **Deterministic Candidate Ingestion (Step 5B)**: Converts candidate graphs into supported standalone `MERGE` statements with embedded properties and integer IDs into HydraDB.
- **Deterministic Graph Candidate Generation (Step 5A)**: Constructs structural graph elements (`Document`, `Channel`, `Message`, `Person`, `Team`) and relationships (`IN_CHANNEL`, `AUTHORED`, `MEMBER_OF`, `PART_OF`) with stable 63-bit integer IDs.
- **Slack Log Parsing & Normalization**: Extracts channel metadata, author, team, and multi-line message threads into structured JSONL documents.

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

5. Run test suite:
   ```bash
   python -m unittest discover tests
   ```
