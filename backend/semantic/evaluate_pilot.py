"""
Deterministic Evaluation of Gemini Semantic Extraction Quality (Step 6D).

Evaluates entity and statement distributions, provenance integrity, confidence,
and generic Entity classification ratios from Gemini pilot results.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "pilot_10_results.jsonl"
)


@dataclass
class PilotEvaluationReport:
    """
    Structured metrics report for semantic extraction evaluation.
    """

    messages_evaluated: int
    entity_type_distribution: dict[str, int]
    statement_type_distribution: dict[str, int]
    empty_entity_count: int
    empty_statement_count: int
    provenance_errors: int
    average_confidence: float
    generic_entity_ratio: float
    total_entities: int
    total_statements: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_results(input_file: Path | str = DEFAULT_INPUT_FILE) -> list[dict[str, Any]]:
    """Load JSONL pilot results file."""
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Pilot results file not found: {path}")

    results: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                results.append(json.loads(line))

    return results


def evaluate_results(results: list[dict[str, Any]]) -> PilotEvaluationReport:
    """
    Compute deterministic quality and distribution metrics from extraction records.
    """
    if not results:
        return PilotEvaluationReport(
            messages_evaluated=0,
            entity_type_distribution={},
            statement_type_distribution={},
            empty_entity_count=0,
            empty_statement_count=0,
            provenance_errors=0,
            average_confidence=0.0,
            generic_entity_ratio=0.0,
            total_entities=0,
            total_statements=0,
        )

    entity_types: Counter[str] = Counter()
    statement_types: Counter[str] = Counter()

    empty_entities = 0
    empty_statements = 0
    provenance_errors = 0
    confidence_values: list[float] = []

    for record in results:
        extraction = record.get("extraction", {})

        # Strict provenance verification
        rec_msg_id = record.get("message_id")
        ext_msg_id = extraction.get("message_id")
        rec_doc_id = record.get("document_id")
        ext_doc_id = extraction.get("document_id")

        if rec_msg_id != ext_msg_id or rec_doc_id != ext_doc_id:
            provenance_errors += 1

        entities = extraction.get("entities", [])
        statements = extraction.get("statements", [])

        if not entities:
            empty_entities += 1

        if not statements:
            empty_statements += 1

        for entity in entities:
            entity_types[entity["type"]] += 1
            if "confidence" in entity:
                confidence_values.append(float(entity["confidence"]))

        for statement in statements:
            statement_types[statement["type"]] += 1
            if "confidence" in statement:
                confidence_values.append(float(statement["confidence"]))

    total_entities = sum(entity_types.values())
    total_statements = sum(statement_types.values())

    generic_count = entity_types.get("Entity", 0)
    generic_ratio = (generic_count / total_entities) if total_entities > 0 else 0.0

    avg_confidence = (
        sum(confidence_values) / len(confidence_values)
        if confidence_values
        else 0.0
    )

    return PilotEvaluationReport(
        messages_evaluated=len(results),
        entity_type_distribution=dict(entity_types.most_common()),
        statement_type_distribution=dict(statement_types.most_common()),
        empty_entity_count=empty_entities,
        empty_statement_count=empty_statements,
        provenance_errors=provenance_errors,
        average_confidence=round(avg_confidence, 3),
        generic_entity_ratio=round(generic_ratio, 4),
        total_entities=total_entities,
        total_statements=total_statements,
    )


def print_evaluation_report(report: PilotEvaluationReport) -> None:
    """Print formatted evaluation summary matching Step 6D expectations."""
    print("=" * 70)
    print("GEMINI PILOT EVALUATION (Step 6D)")
    print("=" * 70)
    print(f"Messages evaluated: {report.messages_evaluated}")

    print("\nEntity types:")
    for name, count in report.entity_type_distribution.items():
        print(f"  {name}: {count}")

    print("\nStatement types:")
    for name, count in report.statement_type_distribution.items():
        print(f"  {name}: {count}")

    print(f"\nMessages with no entities:   {report.empty_entity_count}")
    print(f"Messages with no statements: {report.empty_statement_count}")
    print(f"Provenance errors:           {report.provenance_errors}")
    print(f"Average confidence:          {report.average_confidence:.3f}")

    print("\nPotential taxonomy observations:")
    print(f"  Generic Entity ratio:      {report.generic_entity_ratio:.1%}")
    if report.generic_entity_ratio > 0.5:
        print("  WARNING: generic Entity usage is high.")

    print("\nEvaluation complete.")
    print("=" * 70)


def evaluate_pilot(
    input_file: Path | str = DEFAULT_INPUT_FILE,
) -> PilotEvaluationReport:
    """Load results, compute metrics, and print evaluation summary."""
    results = load_results(input_file)
    report = evaluate_results(results)
    print_evaluation_report(report)
    return report


def main() -> None:
    evaluate_pilot()


if __name__ == "__main__":
    main()