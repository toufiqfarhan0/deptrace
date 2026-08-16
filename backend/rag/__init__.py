"""
Graph RAG Package (Step 8).

Coordinates deterministic HydraDB retrieval and grounded Gemini answer generation.
"""

from __future__ import annotations

from backend.rag.answer_generator import GeminiAnswerGenerator
from backend.rag.models import AnswerRequest, AnswerResponse
from backend.rag.rag_pipeline import GraphRAGPipeline, answer_question

__all__ = [
    "AnswerRequest",
    "AnswerResponse",
    "GeminiAnswerGenerator",
    "GraphRAGPipeline",
    "answer_question",
]
