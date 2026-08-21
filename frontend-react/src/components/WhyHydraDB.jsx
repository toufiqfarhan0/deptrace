import React, { useState, useEffect } from 'react'
import {
  SlackIcon,
  LinearIcon,
  GitHubIcon,
  JiraIcon,
  ConfluenceIcon,
  PagerDutyIcon,
} from './SourceIcons.jsx'

export default function WhyHydraDB({ onNavigateToAsk, onNavigateToTrace, onNavigateToTimeline, onNavigateToConflicts, onNavigateToGraph }) {
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

  const pipelineSteps = [
    {
      badge: '01',
      name: '6-Source Ingestion',
      desc: 'Ingests Slack, Linear, GitHub, Jira, Confluence & PagerDuty events.',
      tag: 'Multi-Source',
    },
    {
      badge: '02',
      name: 'Ontology Mapping',
      desc: 'Extracts typed nodes (PR, Ticket, Service) & semantic graph edges.',
      tag: 'HydraDB Graph',
    },
    {
      badge: '03',
      name: 'Bi-Temporal Replay',
      desc: 'Tracks event occurrence timestamps vs. ingestion transaction times.',
      tag: 'Causal Timeline',
    },
    {
      badge: '04',
      name: 'Truth Arbitration',
      desc: 'Scores source authority: Merged PR (0.95+) > Ticket (0.85) > Chat (0.60).',
      tag: 'Conflict Arbiter',
    },
    {
      badge: '05',
      name: 'Evidence Bundling',
      desc: 'Packages bounded facts [E1, E2, ...] with raw message ID provenance.',
      tag: 'Deterministic [E#]',
    },
    {
      badge: '06',
      name: 'Grounded Synthesis',
      desc: 'LLM strictly synthesizes cited facts with auditable OpenCypher queries.',
      tag: 'Zero Hallucination',
    },
  ]

  const corePillars = [
    {
      num: '01',
      title: 'UNIFIED ENTERPRISE ONTOLOGY',
      tag: '6 Signal Connectors',
      desc: 'Breaks down organizational communication silos by linking Slack conversations, Linear tickets, GitHub PRs/commits, Jira issues, Confluence RFCs, and PagerDuty alerts into a single unified knowledge graph in HydraDB Cloud.',
      cta: 'Explore Graph Canvas',
      action: onNavigateToGraph,
    },
    {
      num: '02',
      title: 'PROVENANCE TRUTH ARBITER',
      tag: 'Authority Hierarchy',
      desc: 'Resolves conflicting engineering claims deterministically. When ephemeral chat panic contradicts merged code, Veridex applies strict source authority weighting (Merged Code 0.95+ > Resolved Ticket 0.85 > Ephemeral Chat 0.60) instead of vector RAG averaging.',
      cta: 'Inspect Truth Arbiter',
      action: onNavigateToConflicts,
    },
    {
      num: '03',
      title: 'BI-TEMPORAL INCIDENT REPLAY',
      tag: 'VCR State Machine',
      desc: 'Reconstructs how incidents unfold step-by-step across time. The dual-time model distinguishes when an event happened from when the team discovered it, enabling dynamic graph playback across Detection, Investigation, Mitigation, and Resolution phases.',
      cta: 'Play Timeline Replay',
      action: onNavigateToTimeline,
    },
    {
      num: '04',
      title: 'MULTI-HOP BLAST RADIUS TRACING',
      tag: 'BFS Graph Traversal',
      desc: 'Traces dependency paths across microservices, configuration parameters, and deployment rollbacks with bounded traversal depth and cycle prevention—computing precise blast radius without LLM-hallucinated links.',
      cta: 'Trace Dependencies',
      action: onNavigateToTrace,
    },
    {
      num: '05',
      title: 'AUDITABLE OPENCYPHER QUERIES',
      tag: 'HydraDB Engine',
      desc: 'Every investigation, dependency trace, and conflict resolution is backed by an auditable OpenCypher query directly inspectable and runnable on HydraDB Cloud, eliminating black-box routing ambiguity.',
      cta: 'Run Ask Query',
      action: onNavigateToAsk,
    },
    {
      num: '06',
      title: 'ZERO-HALLUCINATION GROUNDING',
      tag: 'Bounded [E#] Citations',
      desc: 'Veridex never asks the LLM to search the corpus. HydraDB retrieves the exact subgraph facts, packaging them into bounded evidence bundles [E1, E2, ...]. The LLM is restricted to synthesizing claims strictly citing these evidence tokens.',
      cta: 'Test Grounded QA',
      action: onNavigateToAsk,
    },
  ]

  const comparisonRows = [
    {
      capability: 'Multi-Hop Relationship Reasoning',
      hydra: 'Native graph traversal across services, PRs, and tickets with cycle prevention.',
      vector: 'Fails on disconnected chunk vectors; cannot traverse multi-hop chains reliably.',
      advantage: 'Deterministic Graph Traversal',
    },
    {
      capability: 'Contradiction & Conflict Resolution',
      hydra: 'Deterministic source authority weighting (Merged Code > Linear Ticket > Slack Chat).',
      vector: 'Blurs and averages conflicting chunks, hallucinating consensus between stale and current claims.',
      advantage: 'Authority-Based Truth',
    },
    {
      capability: 'Bi-Temporal Timeline Replay',
      hydra: 'Dual-time state machine: tracks occurrence time vs. transaction ingestion time.',
      vector: 'Loses chronological causality; treats old and new documents as flat embeddings.',
      advantage: 'Chronological Integrity',
    },
    {
      capability: 'Dependency Blast Radius Calculation',
      hydra: 'Computes exact downstream dependency trees up to 5 hops deep.',
      vector: 'Relies on keyword proximity; cannot compute directional blast radius.',
      advantage: 'Exact Graph Blast Radius',
    },
    {
      capability: 'Query Auditability & Transparency',
      hydra: 'Auditable OpenCypher queries with inspectable MATCH and WHERE graph patterns.',
      vector: 'Black-box cosine similarity scores with opaque chunk selection.',
      advantage: 'Inspectable OpenCypher',
    },
    {
      capability: 'Provenance & Hallucination Prevention',
      hydra: '100% bounded evidence bundles with raw message IDs and [E#] citation brackets.',
      vector: 'High risk of synthesis hallucination and unattributed background extrapolation.',
      advantage: '100% Provenance Invariants',
    },
  ]

  return (
    <section aria-label="Why HydraDB architecture and benchmark" className="why-hydra-section">
      <div className="view-header">
        <div className="why-eyebrow-row">
          <span className="why-track-badge">TRACK 01: ENTERPRISE CONTEXT & ONTOLOGY ALIGNMENT</span>
          <span className="why-engine-badge">HYDRADB CLOUD READY</span>
        </div>
        <h1 className="view-title">How Veridex Works</h1>
        <div className="view-subtitle">
          Why deterministic graph reasoning on HydraDB Cloud is essential for enterprise truth, multi-source conflict resolution, and bi-temporal incident replay.
        </div>
      </div>

      {/* 6 Enterprise Source Ingestion Banner */}
      <div className="why-sources-banner">
        <div className="why-sources-label">
          <span>UNIFIED INGESTION FROM 6 ENTERPRISE SYSTEMS:</span>
        </div>
        <div className="why-sources-pills">
          <span className="why-src-pill slack"><SlackIcon size={14} /> Slack Discussions</span>
          <span className="why-src-pill linear"><LinearIcon size={14} /> Linear Issues</span>
          <span className="why-src-pill github"><GitHubIcon size={14} /> GitHub PRs & Commits</span>
          <span className="why-src-pill jira"><JiraIcon size={14} /> Jira Incident Tickets</span>
          <span className="why-src-pill confluence"><ConfluenceIcon size={14} /> Confluence RFCs & ADRs</span>
          <span className="why-src-pill pagerduty"><PagerDutyIcon size={14} /> PagerDuty Alerts</span>
        </div>
      </div>

      {/* Visual Investigation Pipeline */}
      <div className="pipeline-card" style={{ marginBottom: '28px' }}>
        <div className="pipeline-header">
          <span className="section-label">THE 6-STAGE ENTERPRISE GRAPH INTELLIGENCE PIPELINE</span>
        </div>
        <div className="pipeline-flow-steps">
          {pipelineSteps.map((step, idx) => (
            <React.Fragment key={step.badge}>
              <div className="pipeline-step-item">
                <div className="pipeline-step-top">
                  <span className="pipeline-step-badge">{step.badge}</span>
                  <span className="pipeline-step-tag">{step.tag}</span>
                </div>
                <div className="pipeline-step-name">{step.name}</div>
                <div className="pipeline-step-desc">{step.desc}</div>
              </div>
              {idx < pipelineSteps.length - 1 && (
                <div className="pipeline-step-arrow" aria-hidden="true">→</div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Core Architectural Pillars */}
      <div className="section-rule">
        <span className="section-label">THE 6 ARCHITECTURAL PILLARS OF VERIDEX</span>
      </div>

      <div className="why-principles-grid">
        {corePillars.map((p) => (
          <div key={p.num} className="why-principle-card">
            <div className="principle-header-row">
              <span className="principle-number">{p.num} · {p.title}</span>
              <span className="principle-tag">{p.tag}</span>
            </div>
            <div className="principle-body">
              {p.desc}
            </div>
            {p.action && (
              <button
                type="button"
                className="principle-cta-btn"
                onClick={() => p.action && p.action()}
              >
                {p.cta} →
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Head-to-Head Comparison: HydraDB vs Vector RAG */}
      <div className="section-rule" style={{ marginTop: '32px', marginBottom: '16px' }}>
        <span className="section-label">COMPARISON MATRIX: HYDRADB GRAPH RAG VS. NAIVE VECTOR RAG</span>
      </div>

      <div className="comparison-matrix-container">
        <table className="comparison-matrix-table">
          <thead>
            <tr>
              <th style={{ width: '22%' }}>CAPABILITY</th>
              <th style={{ width: '38%' }} className="th-hydra">
                VERIDEX (HYDRADB GRAPH RAG)
              </th>
              <th style={{ width: '40%' }} className="th-vector">
                TRADITIONAL VECTOR / CHUNKING RAG
              </th>
            </tr>
          </thead>
          <tbody>
            {comparisonRows.map((row, idx) => (
              <tr key={idx}>
                <td className="matrix-cap-cell">
                  <strong>{row.capability}</strong>
                  <span className="matrix-badge">{row.advantage}</span>
                </td>
                <td className="matrix-hydra-cell">
                  <div className="matrix-cell-content">
                    <span className="matrix-check">✓</span>
                    <span>{row.hydra}</span>
                  </div>
                </td>
                <td className="matrix-vector-cell">
                  <div className="matrix-cell-content">
                    <span className="matrix-cross">✕</span>
                    <span>{row.vector}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Live Benchmark & Evaluation Report */}
      <div className="section-rule" style={{ marginTop: '36px', marginBottom: '16px' }}>
        <span className="section-label">LIVE HYDRADB BENCHMARK & INVARIANT AUDIT</span>
      </div>

      <div className="benchmark-toolbar">
        <div className="benchmark-subtext">
          Real-time deterministic benchmark executed over the HydraDB Cloud knowledge graph.
        </div>
        <button
          className="query-execute-btn"
          onClick={runEvaluation}
          disabled={loading}
          style={{ padding: '7px 16px', fontSize: '0.74rem', borderRadius: 'var(--radius)' }}
          aria-label="Re-run evaluation benchmark"
        >
          {loading ? 'RUNNING BENCHMARK...' : 'RE-RUN BENCHMARK →'}
        </button>
      </div>

      {loading && (
        <div className="state-block" role="status">
          <div className="loading-card">
            <div className="loading-spinner-ring" />
            <div>
              <div className="loading-title">Executing Benchmark...</div>
              <div className="loading-desc">Running deterministic queries and validating provenance invariants on HydraDB Cloud...</div>
            </div>
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

          <div className="ablation-table-container">
            <table className="ablation-table">
              <thead>
                <tr>
                  <th>INVESTIGATION QUERY</th>
                  <th>GRAPH EVIDENCE</th>
                  <th>NAIVE TEXT SEARCH</th>
                  <th>STRUCTURAL ADVANTAGE</th>
                </tr>
              </thead>
              <tbody>
                {report.ablation_comparisons?.map((ab, idx) => (
                  <tr key={idx}>
                    <td className="ablation-query-cell">
                      {ab.query}
                    </td>
                    <td className="ablation-evidence-cell">
                      {ab.graph_evidence_count} items ({ab.graph_relationships_found.join(', ')})
                    </td>
                    <td className="ablation-naive-cell">
                      {ab.text_matches_count} keyword matches (0 edges)
                    </td>
                    <td className="ablation-advantage-cell">
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
