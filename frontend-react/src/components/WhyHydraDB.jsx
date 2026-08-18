import React, { useState, useEffect } from 'react'

export default function WhyHydraDB() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const runEvaluation = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/evaluation')
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      setReport(data)
    } catch (err) {
      setError(err.message || 'Failed to load evaluation report.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    runEvaluation()
  }, [])

  return (
    <section aria-label="Why HydraDB architecture and benchmark" className="why-hydra-section">
      <div className="view-header">
        <h1 className="view-title">How Veridex Works</h1>
        <div className="view-subtitle">
          Why deterministic graph reasoning with HydraDB is essential for enterprise truth rather than traditional vector RAG.
        </div>
      </div>

      {/* Visual Investigation Pipeline */}
      <div className="pipeline-card" style={{ marginBottom: '24px' }}>
        <div className="pipeline-header">
          <span className="section-label">THE 5-STEP INVESTIGATION PIPELINE</span>
        </div>
        <div className="pipeline-flow-steps">
          <div className="pipeline-step-item">
            <span className="pipeline-step-badge">01</span>
            <div className="pipeline-step-name">User Question</div>
            <div className="pipeline-step-desc">Natural language incident or ticket inquiry</div>
          </div>
          <div className="pipeline-step-arrow" aria-hidden="true">→</div>
          <div className="pipeline-step-item">
            <span className="pipeline-step-badge">02</span>
            <div className="pipeline-step-name">HydraDB Resolution</div>
            <div className="pipeline-step-desc">Graph traversal & relationship resolution</div>
          </div>
          <div className="pipeline-step-arrow" aria-hidden="true">→</div>
          <div className="pipeline-step-item">
            <span className="pipeline-step-badge">03</span>
            <div className="pipeline-step-name">Evidence Bundle</div>
            <div className="pipeline-step-desc">Bounded facts [E1, E2] with doc provenance</div>
          </div>
          <div className="pipeline-step-arrow" aria-hidden="true">→</div>
          <div className="pipeline-step-item">
            <span className="pipeline-step-badge">04</span>
            <div className="pipeline-step-name">Gemini Synthesis</div>
            <div className="pipeline-step-desc">Language generation strictly from evidence</div>
          </div>
          <div className="pipeline-step-arrow" aria-hidden="true">→</div>
          <div className="pipeline-step-item">
            <span className="pipeline-step-badge">05</span>
            <div className="pipeline-step-name">Grounded Answer</div>
            <div className="pipeline-step-desc">Verifiable citations with zero hallucination</div>
          </div>
        </div>
      </div>

      {/* Core Architectural Flow */}
      <div className="section-rule">
        <span className="section-label">THE 5 PRINCIPLES OF VERIDEX GRAPH REASONING</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', marginBottom: '24px' }}>
        <div style={{ border: '1px solid var(--c-border)', background: 'var(--c-surface)', padding: '16px', borderRadius: 'var(--radius)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--c-accent)', fontWeight: 700, marginBottom: '6px' }}>
            01 · DETERMINISTIC RESOLUTION
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--c-text-2)', lineHeight: 1.5 }}>
            Veridex does not ask the LLM to search the corpus. HydraDB resolves typed statements, entity references, and direct <code style={{ color: 'var(--c-accent)' }}>ABOUT</code> relationships deterministically.
          </div>
        </div>

        <div style={{ border: '1px solid var(--c-border)', background: 'var(--c-surface)', padding: '16px', borderRadius: 'var(--radius)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--c-accent)', fontWeight: 700, marginBottom: '6px' }}>
            02 · BOUNDED EVIDENCE BUNDLES
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--c-text-2)', lineHeight: 1.5 }}>
            Retrieval packages discrete graph evidence items <code style={{ color: 'var(--c-accent)' }}>[E1, E2, ...]</code> with strict source message ID and document ID provenance.
          </div>
        </div>

        <div style={{ border: '1px solid var(--c-border)', background: 'var(--c-surface)', padding: '16px', borderRadius: 'var(--radius)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--c-accent)', fontWeight: 700, marginBottom: '6px' }}>
            03 · STRICT GROUNDED SYNTHESIS
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--c-text-2)', lineHeight: 1.5 }}>
            The LLM synthesizes answers exclusively from the supplied graph bundle. Claims must cite their evidence item bracket <code style={{ color: 'var(--c-accent)' }}>[E#]</code>.
          </div>
        </div>

        <div style={{ border: '1px solid var(--c-border)', background: 'var(--c-surface)', padding: '16px', borderRadius: 'var(--radius)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--c-accent)', fontWeight: 700, marginBottom: '6px' }}>
            04 · ZERO-HALLUCINATION TRACING
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--c-text-2)', lineHeight: 1.5 }}>
            Dependency tracing traverses real HydraDB graph paths with cycle protection and bounded depth—no LLM-invented services, authors, or links.
          </div>
        </div>

        <div style={{ border: '1px solid var(--c-border)', background: 'var(--c-surface)', padding: '16px', borderRadius: 'var(--radius)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--c-accent)', fontWeight: 700, marginBottom: '6px' }}>
            05 · VERIFIABLE PROVENANCE
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--c-text-2)', lineHeight: 1.5 }}>
            Every hop, evidence row, and timeline event traces back to the raw message payload in the EnterpriseRAG-Bench dataset.
          </div>
        </div>
      </div>

      {/* Live Benchmark & Evaluation Report */}
      <div className="section-rule">
        <span className="section-label">LIVE HYDRADB BENCHMARK & INVARIANT AUDIT</span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--c-text-3)', fontFamily: 'var(--font-mono)' }}>
          Real-time deterministic benchmark executed over the HydraDB Cloud knowledge graph.
        </div>
        <button
          className="query-execute-btn"
          onClick={runEvaluation}
          disabled={loading}
          style={{ padding: '6px 14px', fontSize: 'var(--text-xs)' }}
          aria-label="Re-run evaluation benchmark"
        >
          {loading ? 'RUNNING BENCHMARK...' : 'RE-RUN BENCHMARK →'}
        </button>
      </div>

      {loading && (
        <div className="state-block" role="status">
          <div className="loading-text">
            Executing deterministic queries on HydraDB
            <div className="loading-dots" aria-hidden="true"><span/><span/><span/></div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-block" role="alert">
          <div className="error-label">Evaluation Error</div>
          <div className="error-desc">{error}</div>
        </div>
      )}

      {report && !loading && (
        <div>
          {/* Top Metric Row */}
          <div className="metrics-row" style={{ marginBottom: '20px' }}>
            <div className="metric-cell">
              <div className="metric-val">{report.total_queries}</div>
              <div className="metric-lbl">Benchmark Queries</div>
            </div>
            <div className="metric-cell">
              <div className="metric-val" style={{ color: 'var(--c-ok)' }}>
                {report.provenance_integrity?.is_valid ? '100%' : 'INVALID'}
              </div>
              <div className="metric-lbl">Provenance Invariants</div>
            </div>
            <div className="metric-cell">
              <div className="metric-val">{report.average_retrieval_latency_ms} ms</div>
              <div className="metric-lbl">Avg Retrieval Latency</div>
            </div>
            <div className="metric-cell">
              <div className="metric-val">{report.average_trace_latency_ms} ms</div>
              <div className="metric-lbl">Avg Trace Latency</div>
            </div>
          </div>

          {/* Ablation Table */}
          <div className="section-rule" style={{ marginTop: '20px', marginBottom: '12px' }}>
            <span className="section-label">ABLATION: HYDRADB GRAPH RETRIEVAL VS. NAIVE TEXT SEARCH</span>
          </div>

          <div style={{ border: '1px solid var(--c-border)', background: 'var(--c-surface)', borderRadius: 'var(--radius)', overflowX: 'auto', marginBottom: '24px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--c-border)', background: 'var(--c-surface-2)', color: 'var(--c-text-3)' }}>
                  <th style={{ padding: '10px 14px' }}>INVESTIGATION QUERY</th>
                  <th style={{ padding: '10px 14px' }}>GRAPH EVIDENCE</th>
                  <th style={{ padding: '10px 14px' }}>NAIVE TEXT SEARCH</th>
                  <th style={{ padding: '10px 14px' }}>STRUCTURAL ADVANTAGE</th>
                </tr>
              </thead>
              <tbody>
                {report.ablation_comparisons?.map((ab, idx) => (
                  <tr key={idx} style={{ borderBottom: idx < report.ablation_comparisons.length - 1 ? '1px solid var(--c-border)' : 'none' }}>
                    <td style={{ padding: '12px 14px', color: 'var(--c-text)', fontWeight: 600, minWidth: '180px' }}>
                      {ab.query}
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--c-ok)', minWidth: '140px' }}>
                      {ab.graph_evidence_count} items ({ab.graph_relationships_found.join(', ')})
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--c-text-3)', minWidth: '140px' }}>
                      {ab.text_matches_count} keyword matches (0 edges)
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--c-text-2)', minWidth: '220px', lineHeight: 1.4 }}>
                      {ab.structural_advantage_summary}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}
