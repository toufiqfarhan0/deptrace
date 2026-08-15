# HydraDB Graph Foundation (Track 1)

This directory contains the canonical graph ontology, schema definitions, validation smoke test, deterministic candidate ingestion, and graph verification queries for the DepTrace EnterpriseRAG-Bench graph layer backed by [HydraDB](https://github.com/hydra-db/hydradb).

---

## Supported Write Pattern

HydraDB's OpenCypher engine currently supports **standalone single-hop relationship `MERGE`**:

```cypher
MERGE
(a:LabelA {id: INTEGER, prop1: 'value1'})
-[:RELATIONSHIP_TYPE {id: INTEGER}]->
(b:LabelB {id: INTEGER, prop2: 'value2'})
```

### Engine Compatibility Rules & Constraints

1. **Integer IDs Required**: All vertex and edge `id` properties must be non-negative integers.
2. **Standalone Node `CREATE` Unsupported**: Standalone node writes like `CREATE (n:Person {id: 1})` are not supported; nodes must be written within a relationship path.
3. **`MATCH + CREATE` Unsupported**: Chaining `MATCH` and `CREATE` in a single query is not currently supported by the query engine.
4. **`MERGE + SET` Unsupported**: `MERGE ... SET n.prop = 'val'` is not currently executable.
5. **Multi-Hop Queries Supported**: Read queries using `MATCH ... WHERE ... RETURN ...` with aliases are fully supported.
6. **Local Storage Engine**: For local development using `MERGE`, start HydraDB with `CLOUD_PROVIDER=memory` due to a known local filesystem storage backend limitation.

---

## Canonical Ontology

Defined in [`schema.py`](file:///C:/Users/toufi/Desktop/deptrace/backend/graph/schema.py):

### Node Labels
- `Person`
- `Team`
- `Channel`
- `Customer`
- `Project`
- `Incident`
- `Message`
- `Document`
- `Decision`
- `ConfigurationChange`
- `Entity`
- `Statement`

### Relationship Types
- `MEMBER_OF`
- `AUTHORED`
- `IN_CHANNEL`
- `PART_OF`
- `MENTIONS`
- `INVOLVED_IN`
- `HAS_INCIDENT`
- `MADE`
- `AFFECTS`
- `SUPPORTED_BY`
- `ABOUT`
- `CONTRADICTS`
- `RESOLVED_BY`
- `INVOLVES`

---

## Running Locally

### 1. Start HydraDB via Docker

```bash
docker run -d --name hydradb \
  -p 8443:8443 \
  -p 7687:7687 \
  -e CLOUD_PROVIDER=memory \
  -e GRAPH_ALLOW_PLAINTEXT=true \
  ghcr.io/hydra-db/hydradb:latest
```

### 2. Set Environment Variables

Retrieve the auth token from your running container:

**PowerShell:**
```powershell
$env:HYDRA_TOKEN = (docker exec hydradb cat /data/auth-token)
$env:HYDRA_URL = "http://127.0.0.1:8443"
```

**Bash:**
```bash
export HYDRA_TOKEN=$(docker exec hydradb cat /data/auth-token)
export HYDRA_URL="http://127.0.0.1:8443"
```

### 3. Execute Smoke Test

```bash
python backend/graph/test_hydra.py
```

### 4. Ingest Candidate Documents (Step 5B)

Ingest the first 10 deterministic candidate documents into HydraDB:

```bash
python backend/graph/ingest_candidates.py
```

### 5. Verify Ingested Graph

Execute multi-hop read queries asserting graph relationships:

```bash
python backend/graph/verify_ingestion.py
```
