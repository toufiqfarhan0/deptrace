import React from 'react'
import { isHydraOnline, getHydraStatusMode, getHydraStatusLabel } from '../utils/hydraStatus.js'

export default function GraphHealth({ hydraStatus }) {
  const isOnline = isHydraOnline(hydraStatus)
  const mode = getHydraStatusMode(hydraStatus)
  const statusText = getHydraStatusLabel(hydraStatus, { format: 'health' })

  const endpoints = [
    { method: 'GET', path: '/api/health', desc: 'HydraDB connectivity & health check' },
    { method: 'POST', path: '/api/ask', desc: 'Deterministic retrieval + grounded synthesis' },
    { method: 'POST', path: '/api/trace', desc: 'Multi-hop BFS dependency tracing' },
    { method: 'GET', path: '/api/trace/entities', desc: 'Graph entity enumeration' },
  ]

  return (
    <section aria-label="Graph health">
      <div className="view-title">Graph Health</div>
      <div className="view-subtitle">
        Live telemetry from HydraDB and backend services. Real metrics only.
      </div>

      <div className="health-grid">
        <div className="health-cell">
          <div className="health-field">HydraDB Status</div>
          <div className={`health-value ${isOnline ? 'ok' : 'err'}`}>
            {statusText}
          </div>
        </div>
        <div className="health-cell">
          <div className="health-field">Knowledge Graph Target</div>
          <div className="health-value">
            {mode === 'cloud' ? 'veridex-hackhydra (Cloud)' : 'default / cell-0 (Local)'}
          </div>
        </div>
        <div className="health-cell">
          <div className="health-field">API Runtime</div>
          <div className="health-value">FastAPI / Uvicorn</div>
        </div>
        <div className="health-cell">
          <div className="health-field">Ingestion Dataset</div>
          <div className="health-value">EnterpriseRAG-Bench (60 Documents)</div>
        </div>
      </div>

      <div className="section-rule" style={{ marginBottom: 12 }}>
        <span className="section-label">ACTIVE API ENDPOINTS</span>
      </div>

      <div style={{ border: '1px solid var(--c-border)', background: 'var(--c-surface)', padding: '0 16px', borderRadius: 'var(--radius)' }}>
        {endpoints.map((ep) => (
          <div key={ep.path} className="endpoint-row">
            <span className="endpoint-method">{ep.method}</span>
            <span className="endpoint-path">{ep.path}</span>
            <span className="endpoint-desc">{ep.desc}</span>
          </div>
        ))}
      </div>

      <div className="section-rule" style={{ marginTop: 24, marginBottom: 12 }}>
        <span className="section-label">PROTOTYPE KNOWLEDGE GRAPH SLICE</span>
      </div>

      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--text-xs)',
          color: 'var(--c-text-2)',
          lineHeight: 1.8,
          border: '1px solid var(--c-border)',
          background: 'var(--c-surface)',
          padding: '16px',
          borderRadius: 'var(--radius)',
        }}
      >
        <div><strong>Dataset:</strong> EnterpriseRAG-Bench (Verified 10-message prototype)</div>
        <div><strong>Semantic Extractions:</strong> 12 verified records</div>
        <div><strong>Entities / Artifacts:</strong> 20 unique components</div>
        <div><strong>Statements:</strong> 37 typed claims, facts, decisions, and actions</div>
        <div><strong>Validated ABOUT Edges:</strong> 8 direct statement-to-entity links</div>
        <div style={{ marginTop: 8, color: 'var(--c-text-3)' }}>
          Note: Structural edges (AUTHORED, MEMBER_OF, IN_CHANNEL) are not present in this semantic slice and are reported as unavailable.
        </div>
      </div>
    </section>
  )
}
