import React, { useState } from 'react';
import { ExplainResponse, TierExplanation } from '../types';

interface Props {
  data: ExplainResponse;
}

export const ExplanationCard: React.FC<Props> = ({ data }) => {
  const [level, setLevel] = useState<'beginner' | 'intermediate' | 'expert'>('intermediate');
  const exp: TierExplanation = data.explanations[level];

  return (
    <div style={{ background: '#1e293b', borderRadius: '12px', padding: '24px', color: '#f8fafc', boxShadow: '0 4px 20px rgba(0,0,0,0.3)', marginBottom: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #334155', paddingBottom: '16px' }}>
        <div>
          <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#38bdf8', fontWeight: 600 }}>
            Domain: {data.detected_domain} · Confidence: {(data.confidence_score * 100).toFixed(0)}%
          </span>
          <h2 style={{ margin: '6px 0 0', fontSize: '1.4rem' }}>Diagnostic Synthesis</h2>
        </div>
        <div style={{ display: 'flex', background: '#0f172a', padding: '4px', borderRadius: '8px' }}>
          {(['beginner', 'intermediate', 'expert'] as const).map((tier) => (
            <button
              key={tier}
              onClick={() => setLevel(tier)}
              style={{
                background: level === tier ? '#0284c7' : 'transparent',
                color: level === tier ? '#ffffff' : '#94a3b8',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 600,
                textTransform: 'capitalize',
                transition: 'all 0.15s ease'
              }}
            >
              {tier}
            </button>
          ))}
        </div>
      </div>

      <div style={{ background: '#0f172a', padding: '16px 20px', borderRadius: '8px', borderLeft: '4px solid #38bdf8', marginBottom: '20px' }}>
        <strong style={{ color: '#38bdf8', display: 'block', fontSize: '0.85rem', marginBottom: '4px' }}>SUMMARY</strong>
        <p style={{ margin: 0, fontSize: '1.05rem', lineHeight: 1.5 }}>{exp.summary}</p>
      </div>

      {exp.analogy && (
        <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px dashed #f59e0b', borderRadius: '8px', padding: '14px 18px', marginBottom: '20px' }}>
          <strong style={{ color: '#fbbf24', display: 'block', fontSize: '0.85rem', marginBottom: '4px' }}>MENTAL MODEL / ANALOGY</strong>
          <p style={{ margin: 0, color: '#fef3c7', fontSize: '0.95rem' }}>{exp.analogy}</p>
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <h4 style={{ color: '#cbd5e1', marginBottom: '8px', fontSize: '0.95rem' }}>Detailed Root Cause Analysis</h4>
        <p style={{ color: '#94a3b8', lineHeight: 1.6, fontSize: '0.95rem' }}>{exp.detailed_explanation}</p>
      </div>

      {exp.code_fix && (
        <div style={{ marginBottom: '20px' }}>
          <h4 style={{ color: '#cbd5e1', marginBottom: '8px', fontSize: '0.95rem' }}>Recommended Code Implementation / Fix</h4>
          <pre style={{ background: '#090d16', padding: '16px', borderRadius: '8px', overflowX: 'auto', color: '#10b981', fontSize: '0.88rem', fontFamily: 'monospace', border: '1px solid #1e293b' }}>
            {exp.code_fix}
          </pre>
        </div>
      )}

      <div>
        <h4 style={{ color: '#cbd5e1', marginBottom: '10px', fontSize: '0.95rem' }}>Remediation Checklist</h4>
        <ul style={{ paddingLeft: '20px', margin: 0, color: '#94a3b8', fontSize: '0.95rem' }}>
          {exp.remediation_steps.map((step, idx) => (
            <li key={idx} style={{ marginBottom: '6px' }}>{step}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};
