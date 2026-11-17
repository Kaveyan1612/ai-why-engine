import React, { useState } from 'react';
import { CausalStep, WhyFollowUpResponse } from '../types';

interface Props {
  initialCauses: CausalStep[];
  queryContext: string;
}

export const CausalExplorer: React.FC<Props> = ({ initialCauses, queryContext }) => {
  const [activeChain, setActiveChain] = useState<{ [key: string]: WhyFollowUpResponse }>({});
  const [loadingKey, setLoadingKey] = useState<string | null>(null);

  const handleDrillWhy = async (step: CausalStep) => {
    if (activeChain[step.step_id]) return;
    setLoadingKey(step.step_id);

    try {
      const res = await fetch('http://localhost:8000/api/v1/why', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          claim_id: step.step_id,
          claim_text: step.claim,
          query_context: queryContext,
          current_depth: 1
        })
      });
      if (res.ok) {
        const data: WhyFollowUpResponse = await res.json();
        setActiveChain((prev) => ({ ...prev, [step.step_id]: data }));
      }
    } catch (e) {
      console.error('Failed to expand Why node', e);
    } finally {
      setLoadingKey(null);
    }
  };

  return (
    <div style={{ background: '#1e293b', borderRadius: '12px', padding: '24px', color: '#f8fafc', boxShadow: '0 4px 20px rgba(0,0,0,0.3)', marginBottom: '24px' }}>
      <h3 style={{ margin: '0 0 16px', fontSize: '1.25rem', color: '#f1f5f9' }}>
        Interactive Causal "Why?" Decomposition
      </h3>
      <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '20px' }}>
        Click on any causal node to recursively investigate: <em style={{ color: '#38bdf8' }}>"Why did this condition happen?"</em>
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {initialCauses.map((step) => {
          const subResult = activeChain[step.step_id];
          const isLoading = loadingKey === step.step_id;

          return (
            <div key={step.step_id} style={{ border: '1px solid #334155', borderRadius: '8px', padding: '16px', background: '#0f172a' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>CONFIDENCE: {(step.confidence * 100).toFixed(0)}%</span>
                  <div style={{ fontSize: '1.05rem', fontWeight: 600, color: '#e2e8f0', marginTop: '2px' }}>
                    {step.claim}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '4px' }}>
                    Evidence: {step.evidence}
                  </div>
                </div>
                <button
                  onClick={() => handleDrillWhy(step)}
                  disabled={isLoading || !!subResult}
                  style={{
                    background: subResult ? '#334155' : '#0284c7',
                    color: subResult ? '#94a3b8' : '#ffffff',
                    border: 'none',
                    padding: '8px 14px',
                    borderRadius: '6px',
                    cursor: subResult ? 'default' : 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    marginLeft: '16px'
                  }}
                >
                  {isLoading ? 'Reasoning…' : subResult ? '✓ Explored' : 'Ask "Why?" →'}
                </button>
              </div>

              {subResult && (
                <div style={{ marginTop: '16px', paddingLeft: '16px', borderLeft: '2px dashed #0284c7' }}>
                  <div style={{ fontSize: '0.82rem', color: '#38bdf8', fontWeight: 600, marginBottom: '6px' }}>
                    SUB-CAUSAL DRILLDOWN (DEPTH {subResult.depth}):
                  </div>
                  <p style={{ margin: '0 0 10px', fontSize: '0.9rem', color: '#cbd5e1' }}>
                    {subResult.scientific_basis}
                  </p>
                  <div style={{ background: '#1e293b', padding: '10px 14px', borderRadius: '6px', fontSize: '0.82rem', color: '#a5f3fc' }}>
                    <strong>Recommended Diagnostic Check:</strong> {subResult.suggested_verification}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
