import React, { useState } from 'react';
import { ExplainResponse } from './types';
import { ExplanationCard } from './components/ExplanationCard';
import { CausalExplorer } from './components/CausalExplorer';

const SAMPLE_INCIDENTS = [
  {
    label: "Linux OOM Container Killed (Exit 137)",
    query: "Task worker-api-79b8c was terminated with signal SIGKILL (exit code 137). cgroup memory.max exceeded 4096MB."
  },
  {
    label: "PyTorch CUDA Out of Memory",
    query: "RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB (GPU 0; 15.78 GiB total capacity; 14.12 GiB already allocated by PyTorch caching allocator)."
  },
  {
    label: "SIGSEGV 11 Null Pointer Access",
    query: "Fatal error: Segmentation fault (core dumped). Signal 11 at rip 0x000055a1b32f dereferencing null address 0x00000000."
  },
  {
    label: "Thread Deadlock Inversion",
    query: "HTTP 504 Gateway Timeout across worker thread pool. Thread 1 waiting on Mutex A (held by Thread 2). Thread 2 waiting on Mutex B (held by Thread 1)."
  }
];

export const App: React.FC = () => {
  const [query, setQuery] = useState(SAMPLE_INCIDENTS[0].query);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExplainResponse | null>(null);

  const handleExplain = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      if (res.ok) {
        const data: ExplainResponse = await res.json();
        setResult(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#090d16', color: '#f8fafc', padding: '40px 20px', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <header style={{ marginBottom: '32px', textAlign: 'center' }}>
          <h1 style={{ fontSize: '2.4rem', fontWeight: 800, margin: '0 0 10px', background: 'linear-gradient(135deg, #38bdf8, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            AI Why? Engine
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '1.05rem', margin: 0 }}>
            Interactive AI explainability and causal diagnostic reasoning workbench powered by Hybrid RAG.
          </p>
        </header>

        {/* Input Console */}
        <div style={{ background: '#1e293b', borderRadius: '12px', padding: '24px', marginBottom: '24px', boxShadow: '0 4px 20px rgba(0,0,0,0.3)' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' }}>
            Pre-loaded Technical Failure Scenarios
          </label>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
            {SAMPLE_INCIDENTS.map((item, i) => (
              <button
                key={i}
                onClick={() => setQuery(item.query)}
                style={{
                  background: query === item.query ? '#0284c7' : '#0f172a',
                  color: query === item.query ? '#ffffff' : '#94a3b8',
                  border: '1px solid #334155',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.82rem',
                  fontWeight: 500
                }}
              >
                {item.label}
              </button>
            ))}
          </div>

          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={4}
            placeholder="Paste your stack trace, compiler error, system anomaly, or test failure..."
            style={{
              width: '100%',
              boxSizing: 'border-box',
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              padding: '14px',
              color: '#f8fafc',
              fontFamily: 'monospace',
              fontSize: '0.92rem',
              lineHeight: 1.5,
              resize: 'vertical',
              marginBottom: '16px'
            }}
          />

          <button
            onClick={handleExplain}
            disabled={loading}
            style={{
              background: 'linear-gradient(135deg, #0284c7, #4f46e5)',
              color: '#ffffff',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            {loading ? 'Synthesizing Causal Diagnostics…' : 'Generate Multi-Tier "Why?" Diagnostic →'}
          </button>
        </div>

        {/* Results */}
        {result && (
          <div>
            <ExplanationCard data={result} />
            <CausalExplorer initialCauses={result.initial_causes} queryContext={result.query} />

            {/* Citations */}
            <div style={{ background: '#1e293b', borderRadius: '12px', padding: '24px', color: '#f8fafc', boxShadow: '0 4px 20px rgba(0,0,0,0.3)' }}>
              <h3 style={{ margin: '0 0 16px', fontSize: '1.15rem', color: '#f1f5f9' }}>
                Retrieved RAG Knowledge Citations
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                {result.citations.map((c) => (
                  <div key={c.doc_id} style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 600 }}>{c.doc_id}</span>
                      <span style={{ fontSize: '0.75rem', color: '#10b981' }}>Relevance: {(c.relevance_score * 100).toFixed(0)}%</span>
                    </div>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#e2e8f0', marginBottom: '8px' }}>
                      {c.title}
                    </div>
                    <p style={{ margin: 0, fontSize: '0.82rem', color: '#94a3b8', lineHeight: 1.5 }}>
                      {c.excerpt}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
