import React, { useState, useEffect, useCallback, useRef } from 'react'
import { getQuickTraceEntities } from '../data/suggestions.js'

function DepPath({ data, onSelectEntity, onNavigateToAsk }) {
  const { root_entity, impact_summary } = data
  const linked = impact_summary?.affected_components || []

  return (
    <div className="dep-path-block">
      <div className="dep-path-entities">
        <div className="dep-root-wrapper">
          <span className="dep-entity-root">{root_entity}</span>
          {onNavigateToAsk && (
            <button
              className="inline-ask-btn"
              onClick={() => onNavigateToAsk(`What happened with ${root_entity}?`)}
              title={`Ask questions about ${root_entity}`}
              aria-label={`Ask questions about ${root_entity}`}
              type="button"
            >
              <span>ASK</span>
              <span aria-hidden="true">→</span>
            </button>
          )}
        </div>

        {linked.map((e) => (
          <div key={e} className="dep-linked-wrapper">
            <span className="dep-arrow" aria-hidden="true">⟷</span>
            <button
              className="dep-entity-linked"
              onClick={() => onSelectEntity(e)}
              aria-label={`Trace ${e}`}
              title={`Trace dependencies for ${e}`}
              type="button"
            >
              {e}
            </button>
            {onNavigateToAsk && (
              <button
                className="inline-ask-btn"
                onClick={() => onNavigateToAsk(`What is connected to ${e}?`)}
                title={`Ask questions about ${e}`}
                aria-label={`Ask questions about ${e}`}
                type="button"
              >
                <span>ASK</span>
              </button>
            )}
          </div>
        ))}
      </div>

      <div className="dep-affected-row">
        <span className="dep-affected-lbl">AFFECTED COMPONENTS:</span>
        {linked.length > 0 ? (
          <div className="dep-affected-list">
            {linked.map((e) => (
              <span key={e} className="dep-affected-tag">
                {e}
              </span>
            ))}
          </div>
        ) : (
          <span className="unavailable-field">No secondary components reached within depth limit</span>
        )}
      </div>
    </div>
  )
}

export default function TraceView({
  initialEntity = '',
  onEntityChange,
  onNavigateToAsk,
}) {
  const [entity, setEntity] = useState(initialEntity)
  const [depth, setDepth] = useState('2')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [latencyMs, setLatencyMs] = useState(null)
  const inputRef = useRef(null)

  const quickEntities = getQuickTraceEntities()

  const handleTrace = useCallback(async (targetOverride) => {
    const target = (targetOverride !== undefined ? targetOverride : entity).trim()
    if (!target) return
    setLoading(true)
    setError(null)
    setResult(null)
    const t0 = performance.now()
    try {
      const res = await fetch('/api/trace', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entity: target, max_depth: parseInt(depth, 10), limit: 25 }),
      })
      const data = await res.json()
      const t1 = performance.now()
      setLatencyMs(Math.round(t1 - t0))
      if (!res.ok) throw new Error(data.detail || data.error || `HTTP ${res.status}`)
      if (!data.found) throw new Error(data.error || `Entity '${target}' not found in knowledge graph.`)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Dependency trace failed.')
    } finally {
      setLoading(false)
    }
  }, [entity, depth])

  // Sync draft entity from external navigation WITHOUT auto-executing
  useEffect(() => {
    if (initialEntity !== undefined) {
      setEntity(initialEntity)
    }
  }, [initialEntity])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleTrace()
    }
  }

  const handleSelectQuickEntity = (ent) => {
    setEntity(ent)
    onEntityChange?.(ent)
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }

  const summary = result?.impact_summary

  return (
    <section aria-label="Dependency trace workspace" className="trace-section">
      <div className="view-header">
        <h1 className="view-title">Trace Dependencies</h1>
        <div className="view-subtitle">
          Follow the relationships behind an incident, ticket, pull request, or engineering decision across HydraDB.
        </div>
      </div>

      {/* Trace Input Card */}
      <div className="query-console" role="search">
        <div className="query-card-header">
          <label htmlFor="trace-target-input" className="query-card-label">
            Target Entity to Trace
          </label>
        </div>
        <div className="trace-input-row">
          <input
            id="trace-target-input"
            ref={inputRef}
            className="trace-input"
            type="text"
            value={entity}
            onChange={(e) => {
              setEntity(e.target.value)
              onEntityChange?.(e.target.value)
            }}
            onKeyDown={handleKeyDown}
            placeholder="Enter an entity such as PR-99501, INC-2026, or ENG-68910..."
            aria-label="Entity to trace"
            disabled={loading}
          />
          <div className="depth-control">
            <label htmlFor="depth-select">Traversal Depth:</label>
            <select
              id="depth-select"
              className="depth-select"
              value={depth}
              onChange={(e) => setDepth(e.target.value)}
              aria-label="Traversal depth"
            >
              <option value="1">1 hop — Direct connections</option>
              <option value="2">2 hops — Secondary dependencies</option>
              <option value="3">3 hops — Full dependency network</option>
            </select>
          </div>
          <button
            className={`query-execute-btn ${loading ? 'loading' : ''}`}
            onClick={() => handleTrace()}
            disabled={loading || !entity.trim()}
            aria-label="Trace dependencies"
            type="button"
          >
            {loading ? (
              <>
                <span className="btn-spinner" aria-hidden="true" />
                <span>TRACING...</span>
              </>
            ) : (
              <>
                <span>TRACE DEPENDENCIES</span>
                <span aria-hidden="true">→</span>
              </>
            )}
          </button>
        </div>

        {/* Quick select popular entities */}
        <div className="trace-quick-select" aria-label="Popular entities to trace">
          <span className="suggestion-prefix">Popular entities:</span>
          <div className="suggestion-pills">
            {quickEntities.map((e) => (
              <button
                key={e}
                className="suggestion-btn"
                onClick={() => handleSelectQuickEntity(e)}
                aria-label={`Select entity ${e}`}
                type="button"
              >
                <span>{e}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="state-block loading-state" role="status" aria-live="polite">
          <div className="loading-card">
            <div className="loading-spinner-ring" aria-hidden="true" />
            <div className="loading-content">
              <div className="loading-title">TRACING GRAPH DEPENDENCIES</div>
              <div className="loading-desc">
                Traversing multi-hop relationships and building chronological timeline in HydraDB...
              </div>
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
        <div className="result-area">
          {/* Summary Section */}
          <div className="query-meta-bar">
            <div className="query-meta-left">
              <span className="query-label-small">ROOT ENTITY</span>
              <span className="query-text-display">{result.root_entity}</span>
            </div>
            {latencyMs !== null && (
              <div className="query-latency-tag">
                <span className="latency-lbl">LATENCY</span>
                <span className="latency-val">{latencyMs} ms</span>
              </div>
            )}
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
            <DepPath
              data={result}
              onSelectEntity={(ent) => {
                setEntity(ent)
                handleTrace(ent)
              }}
              onNavigateToAsk={onNavigateToAsk}
            />
          </div>

          {/* Statement Breakdown */}
          {summary?.statements_by_type && Object.keys(summary.statements_by_type).length > 0 && (
            <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
              {Object.entries(summary.statements_by_type).map(([type, count]) => (
                <span key={type} className={`type-badge ${type}`}>
                  {count} {type}{count !== 1 ? 's' : ''}
                </span>
              ))}
            </div>
          )}

          {/* Chronological Statement Timeline */}
          <div className="evidence-block">
            <div className="evidence-header">
              <div className="evidence-header-left">
                <span className="evidence-header-label">RECONSTRUCTED TIMELINE</span>
                <span className="evidence-count">
                  {result.timeline?.length ?? 0} chronological event{result.timeline?.length === 1 ? '' : 's'}
                </span>
              </div>
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
                        <span className="timeline-entity-tag">
                          {item.associated_entity}
                        </span>
                      </div>
                      <div className="timeline-statement">{item.statement}</div>
                      <div className="timeline-provenance">
                        <span><strong>Message ID:</strong> {item.message_id}</span>
                        <span>
                          <strong>Document:</strong>{' '}
                          <span title={item.document_id}>
                            {item.document_id?.length > 25 ? `${item.document_id.slice(0, 25)}...` : item.document_id}
                          </span>
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
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && !error && (
        <div className="empty-block starter-empty-block">
          <div className="starter-header">
            <div className="empty-label">TRACE GRAPH DEPENDENCIES</div>
            <div className="empty-desc">
              Select a popular entity or enter a ticket/PR above to trace upstream causes, downstream affected services,
              and chronologically ordered actions across the HydraDB knowledge graph.
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
