from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ExplainRequest(BaseModel):
    query: str = Field(..., description="The error, stack trace, or anomaly to explain")
    context: Optional[str] = Field(None, description="Optional extra system context or logs")
    category: Optional[str] = Field("general", description="Category: systems, ml, network, database, concurrency")

class CausalStep(BaseModel):
    step_id: str
    claim: str
    sub_causes: List[str] = Field(default_factory=list)
    confidence: float
    evidence: str

class TierExplanation(BaseModel):
    level: str  # beginner, intermediate, expert
    summary: str
    detailed_explanation: str
    analogy: Optional[str] = None
    architectural_impact: Optional[str] = None
    root_cause_analysis: str
    remediation_steps: List[str]
    code_fix: Optional[str] = None

class DocumentCitation(BaseModel):
    doc_id: str
    title: str
    source: str
    relevance_score: float
    excerpt: str

class ExplainResponse(BaseModel):
    query: str
    detected_domain: str
    confidence_score: float
    explanations: Dict[str, TierExplanation]
    citations: List[DocumentCitation]
    causal_root_id: str
    initial_causes: List[CausalStep]

class WhyFollowUpRequest(BaseModel):
    claim_id: str
    claim_text: str
    query_context: str
    current_depth: int = 1

class WhyFollowUpResponse(BaseModel):
    claim_id: str
    claim_text: str
    depth: int
    direct_causes: List[CausalStep]
    scientific_basis: str
    suggested_verification: str
