export interface TierExplanation {
  level: 'beginner' | 'intermediate' | 'expert';
  summary: str;
  detailed_explanation: string;
  analogy?: string;
  architectural_impact?: string;
  root_cause_analysis: string;
  remediation_steps: string[];
  code_fix?: string;
}

export interface DocumentCitation {
  doc_id: string;
  title: string;
  source: string;
  relevance_score: number;
  excerpt: string;
}

export interface CausalStep {
  step_id: string;
  claim: string;
  sub_causes: string[];
  confidence: number;
  evidence: string;
}

export interface ExplainResponse {
  query: string;
  detected_domain: string;
  confidence_score: number;
  explanations: Record<'beginner' | 'intermediate' | 'expert', TierExplanation>;
  citations: DocumentCitation[];
  causal_root_id: string;
  initial_causes: CausalStep[];
}

export interface WhyFollowUpResponse {
  claim_id: string;
  claim_text: string;
  depth: number;
  direct_causes: CausalStep[];
  scientific_basis: string;
  suggested_verification: string;
}
