"""
Unit & Integration Tests for AI Why? Engine.
Tests Hybrid RAG retrieval, Multi-tier explanations, and Recursive 'Why?' traversal.
"""

import pytest
from app.engine.rag_retriever import HybridRetriever
from app.engine.explainer import MultiTierExplainer
from app.engine.causal_graph import CausalGraphEngine
from app.engine.corpus import KNOWLEDGE_CORPUS

def test_hybrid_retriever_oom():
    retriever = HybridRetriever(KNOWLEDGE_CORPUS)
    citations = retriever.retrieve("Process terminated exit code 137 OOMKilled cgroup", top_k=2)
    assert len(citations) > 0
    assert "OOM" in citations[0].title or "Memory" in citations[0].title
    assert citations[0].relevance_score > 0.6

def test_hybrid_retriever_cuda():
    retriever = HybridRetriever(KNOWLEDGE_CORPUS)
    citations = retriever.retrieve("RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB", top_k=2)
    assert len(citations) > 0
    assert "CUDA" in citations[0].title or "PyTorch" in citations[0].title

def test_multi_tier_explainer_structure():
    explainer = MultiTierExplainer()
    retriever = HybridRetriever(KNOWLEDGE_CORPUS)
    citations = retriever.retrieve("SIGSEGV Segmentation fault null pointer", top_k=2)
    explanations = explainer.explain("SIGSEGV Segmentation fault null pointer", citations)

    assert "beginner" in explanations
    assert "intermediate" in explanations
    assert "expert" in explanations

    # Beginner should have analogy
    assert explanations["beginner"].analogy is not None
    # Expert should have deep root cause analysis and remediation
    assert len(explanations["expert"].remediation_steps) >= 3
    assert explanations["expert"].code_fix is not None

def test_causal_graph_why_followup():
    engine = CausalGraphEngine()
    initial = engine.get_initial_causes("CUDA Out of memory on GPU")
    assert len(initial) > 0

    first_cause = initial[0]
    followup = engine.explore_why(first_cause.step_id, first_cause.claim, depth=1)
    assert followup.depth == 2
    assert followup.scientific_basis != ""
    assert followup.suggested_verification != ""
