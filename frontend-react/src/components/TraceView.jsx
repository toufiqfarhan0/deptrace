import React, { useState, useEffect, useCallback } from 'react'

const QUICK_ENTITIES = [
  'REL-311',
  'kernel-selector',
  'api-search',
  'kernel-fallback policy',
  'request-time guard',
  'v3.1.1-legacy-tokenizer',
]

function DepPath({ data, onSelectEntity }) {
  const { root_entity, impact_summary } = data
  const linked = impact_summary?.affected_components || []

  return (
    <div className="dep-path-block">
      <div className="dep-path-entities">
        <span className="dep-entity-root">{root_entity}</span>
        {linked.map((e) => (
          <span key={e} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="dep-arrow">⟷</span>
            <button
              className="dep-entity-linked"
              onClick={() => onSelectEntity(e)}
              aria-label={`Trace ${e}`}
            >
              {e}
            </button>
          </span>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10, alignItems: 'center' }}>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--c-text-3)', fontFamily: 'var(--font-mono)' }}>
          AFFECTED COMPONENTS:
        </span>
        {linked.length > 0 ? (
          linked.map((e, idx) => (
            <span key={e} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--c-text-2)', fontFamily: 'var(--font-mono)' }}>
                {e}
              </span>
              {idx < linked.length - 1 && <span style={{ color: 'var(--c-text-3)' }}>·</span>}
            </span>
          ))
        ) : (
          <span className="unavailable-field">No secondary components reached within depth limit</span>
        )}
      </div>
    </div>
  )
}

function UnavailableField({ label }) {
  return (
    <div style={{ display: 'flex', gap: 8, marginBottom: 4, alignItems: 'center' }}>
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--c-text-3)', fontFamily: 'var(--font-mono)', minWidth: 80 }}>
        {label}:
      </span>
      <span className="unavailable-field">Not available in current graph</span>
    </div>
  )
}

export default function TraceView({ initialEntity, onEntityChange }) {
  const [entity, setEntity] = useState(initialEntity || '')
  const [depth, setDepth] = useState('2')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (initialEntity && initialEntity !== entity) {
      setEntity(initialEntity)
    }
  }, [initialEntity])

  const handleTrace = useCallback(async (targetOverride) => {
    const target = (targetOverride || entity).trim()
    if (!target) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch('/api/trace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity: target, max_depth: parseInt(depth, 10), limit: 25 }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || data.error || `HTTP ${res.status}`)
      if (!data.found) throw new Error(data.error || `Entity '${target}' not found in knowledge graph.`)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Dependency trace failed.')
    } finally {
      setLoading(false)
    }
  }, [entity, depth])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleTrace()
    }
  }

  const handleSelectQuickEntity = (ent) => {
    setEntity(ent)
    onEntityChange?.(ent)
    handleTrace(ent)
  }

  const summary = result?.impact_summary

  return (
    <section aria-label="Dependency trace workspace">
      <div className="view-title">Trace</div>
      <div className="view-subtitle">
        Trace multi-hop technical dependencies, co-occurring incident artifacts, and chronological statements.
      </div>

      {/* Trace Input */}
      <div style={{ marginBottom: 28 }}>
        <div className="trace-input-row">
          <input
            className="trace-input"
            type="text"
            value={entity}
            onChange={(e) => {
              setEntity(e.target.value)
              onEntityChange?.(e.target.value)
            }}
            onKeyDown={handleKeyDown}
            placeholder="Entity to trace: REL-311, kernel-selector, api-search..."
            aria-label="Entity to trace"
            disabled={loading}
          />
          <div className="depth-control">
            <label htmlFor="depth-select">Depth:</label>
            <select
              id="depth-select"
              className="depth-select"
              value={depth}
              onChange={(e) => setDepth(e.target.value)}
              aria-label="Traversal depth"
            >
              <option value="1">1 hop</option>
              <option value="2">2 hops</option>
              <option value="3">3 hops</option>
            </select>
          </div>
          <button
            className="trace-btn"
            onClick={() => handleTrace()}
            disabled={loading || !entity.trim()}
            aria-label="Execute dependency trace"
          >
            {loading ? '...' : 'TRACE →'}
          </button>
        </div>
        <div className="trace-quick-select">
          <span className="suggestion-prefix">Quick select:</span>
          {QUICK_ENTITIES.map((e, i) => (
            <span key={e} style={{ display: 'flex', alignItems: 'center' }}>
              <button
                className="suggestion-btn"
                onClick={() => handleSelectQuickEntity(e)}
                aria-label={`Trace ${e}`}
              >
                {e}
              </button>
              {i < QUICK_ENTITIES.length - 1 && <span className="suggestion-sep">·</span>}
            </span>
          ))}
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="state-block" role="status" aria-live="polite">
          <div className="loading-text">
            Traversing HydraDB graph
            <div className="loading-dots" aria-hidden="true">
              <span/><span/><span/>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="error-block" role="alert">
          <div className="error-label">Trace Error</div>
          <div className="error-desc">{error}</div>
        </div>
      )}

      {/* Result */}
      {result && !loading && (
        <div>
          {/* IMPACT SECTION */}
          <div className="section-rule">
            <span className="section-label">TRACE: {result.root_entity}</span>
          </div>

          <div className="impact-section">
            <div className="metrics-row">
              <div className="metric-cell">
                <div className="metric-val">{summary?.total_linked_entities ?? 0}</div>
                <div className="metric-lbl">Linked Components</div>
              </div>
              <div className="metric-cell">
                <div className="metric-val">{summary?.total_statements ?? 0}</div>
                <div className="metric-lbl">Statements</div>
              </div>
              <div className="metric-cell">
                <div className="metric-val">{summary?.traversal_depth ?? 0}</div>
                <div className="metric-lbl">Hops Traversed</div>
              </div>
              <div className="metric-cell">
                <div className="metric-val">{summary?.affected_messages?.length ?? 0}</div>
                <div className="metric-lbl">Source Messages</div>
              </div>
            </div>

            {/* Dependency Path Representation */}
            <DepPath data={result} onSelectEntity={handleSelectQuickEntity} />

            {/* Structural Fields Availability */}
            <div style={{ marginTop: 12 }}>
              <UnavailableField label="AUTHORS" />
              <UnavailableField label="TEAMS" />
              <UnavailableField label="CHANNELS" />
            </div>
          </div>

          {/* Statement Breakdown */}
          {summary?.statements_by_type && Object.keys(summary.statements_by_type).length > 0 && (
            <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
              {Object.entries(summary.statements_by_type).map(([type, count]) => (
                <span key={type} className={`type-badge ${type}`}>
                  {count} {type}{count !== 1 ? 's' : ''}
                </span>
              ))}
            </div>
          )}

          {/* Chronological Statement Timeline */}
          <div className="section-rule">
            <span className="section-label">CHRONOLOGICAL STATEMENT TIMELINE</span>
          </div>

          {result.timeline && result.timeline.length > 0 ? (
            <div className="timeline-rows">
              {result.timeline.map((item) => (
                <div key={`${item.order_index}-${item.statement}`} className="timeline-row">
                  <div className="timeline-index">
                    {String(item.order_index).padStart(2, '0')}
                  </div>
                  <div className="timeline-content">
                    <div className="timeline-meta-row">
                      <span className={`type-badge ${item.statement_type}`}>
                        {item.statement_type?.toUpperCase()}
                      </span>
                      <span className="type-badge rel">{item.relationship}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--c-text-2)' }}>
                        {item.associated_entity}
                      </span>
                    </div>
                    <div className="timeline-statement">{item.statement}</div>
                    <div className="timeline-provenance">
                      <span><strong>msg:</strong> {item.message_id}</span>
                      <span>
                        <strong>doc:</strong> {item.document_id?.length > 25 ? `${item.document_id.slice(0, 25)}...` : item.document_id}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-block">
              <div className="empty-label">No Timeline Statements</div>
              <div className="empty-desc">No statements recorded along this dependency path.</div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && !error && (
        <div className="empty-block">
          <div className="empty-label">Trace Ready</div>
          <div className="empty-desc">
            Select or enter an entity above to trace upstream causes, downstream affected services,
            and chronologically ordered actions from the HydraDB graph.
          </div>
        </div>
      )}
    </section>
  )
}
