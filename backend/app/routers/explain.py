"""
FastAPI Router for Explainability, RAG Retrieval, and "Why?" follow-up exploration.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    ExplainRequest, ExplainResponse, WhyFollowUpRequest, WhyFollowUpResponse
)
from app.engine.rag_retriever import HybridRetriever
from app.engine.explainer import MultiTierExplainer
from app.engine.causal_graph import CausalGraphEngine
from app.engine.corpus import KNOWLEDGE_CORPUS

router = APIRouter(prefix="/api/v1", tags=["Explainability"])

# Singleton engines
retriever = HybridRetriever(KNOWLEDGE_CORPUS)
explainer = MultiTierExplainer()
causal_engine = CausalGraphEngine()

@router.post("/explain", response_model=ExplainResponse)
async def generate_explanation(request: ExplainRequest):
    """
    Generate multi-tier (Beginner, Intermediate, Expert) explanations using
    Hybrid RAG retrieval and causal decomposition.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 1. Hybrid RAG retrieval
    citations = retriever.retrieve(request.query, top_k=3)

    # 2. Multi-tier synthesis
    explanations = explainer.explain(request.query, citations)

    # 3. Initial causal breakdown
    initial_causes = causal_engine.get_initial_causes(request.query)

    # Detect domain
    domain = "systems"
    q_low = request.query.lower()
    if "cuda" in q_low or "torch" in q_low or "gpu" in q_low:
        domain = "machine_learning"
    elif "deadlock" in q_low or "mutex" in q_low:
        domain = "concurrency"
    elif "sigsegv" in q_low or "segmentation" in q_low:
        domain = "memory_management"

    return ExplainResponse(
        query=request.query,
        detected_domain=domain,
        confidence_score=0.94,
        explanations=explanations,
        citations=citations,
        causal_root_id=initial_causes[0].step_id if initial_causes else "root",
        initial_causes=initial_causes
    )

@router.post("/why", response_model=WhyFollowUpResponse)
async def follow_up_why(request: WhyFollowUpRequest):
    """
    Recursive 'Why?' reasoning endpoint allowing interactive causal tree drilldown.
    """
    if not request.claim_id:
        raise HTTPException(status_code=400, detail="claim_id is required")

    return causal_engine.explore_why(
        claim_id=request.claim_id,
        claim_text=request.claim_text,
        depth=request.current_depth + 1
    )

@router.get("/corpus")
async def list_corpus():
    """
    Return domain knowledge corpus metadata.
    """
    return {
        "total_documents": len(KNOWLEDGE_CORPUS),
        "documents": [
            {"id": d["id"], "title": d["title"], "domain": d["domain"], "keywords": d["keywords"]}
            for d in KNOWLEDGE_CORPUS
        ]
    }
