# DepTrace

DepTrace is an Enterprise RAG (Retrieval-Augmented Generation) and Dependency Tracing system designed to analyze cross-team discussions, operational issues, and engineering dependency chains.

## Project Structure

```
deptrace/
├── backend/
│   └── ingestion/
│       └── parse_slack.py        # Slack dump parser converting text threads to JSONL
├── data/
│   └── enterprise-rag/
│       ├── parsed/
│       │   └── slack.jsonl       # Structured JSONL records parsed from Slack logs
│       ├── slack/                # Raw exported Slack channel logs (.txt)
│       ├── questions.jsonl       # Benchmark/evaluation questions and ground truth facts
│       └── slack_slice_0001.zip  # Compressed raw archive slice
├── frontend/                     # DepTrace UI client
└── .gitignore
```

## Features

- **Slack Log Parsing & Normalization**: Extracts channel metadata, author, team, and multi-line message threads into structured JSONL documents.
- **Enterprise RAG Dataset**: Ground truth benchmark questions and facts for evaluating RAG retrieval and synthesis accuracy.

## Getting Started

### Prerequisites

- Python 3.9+

### Ingestion

To parse raw Slack export files into structured JSONL:

```bash
python backend/ingestion/parse_slack.py
```
