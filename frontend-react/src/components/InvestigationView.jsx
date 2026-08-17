import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react'
import { getInquiryQueries } from '../data/suggestions.js'

const STARTER_QUERIES = [
  'What happened during incident INC-2026?',
  'What is PR-99501 about?',
  'What is ENG-68910 about?',
]

function CitationPill({ id, onClick, highlighted }) {
  return (
    <button
      className={`citation-pill ${highlighted ? 'highlighted' : ''}`}
      onClick={() => onClick(id)}
      aria-label={`Jump to evidence [${id}]`}
      type="button"
    >
      [{id}]
    </button>
  )
}

function formatAnswerWithCitations(answer, onCitationClick, highlightedId) {
  if (!answer) return null
  // Parse grouped citations like [E1, E2] or [E1]
  const parts = answer.split(/(\[[^\]]*E\d+[^\]]*\])/gi)
  return parts.map((part, i) => {
    const citMatch = part.match(/^\[(.*?)\]$/)
    if (citMatch) {
      const eMatches = citMatch[1].match(/E\d+/gi)
      if (eMatches && eMatches.length > 0) {
        return (
          <span key={i} className="citation-group">
            {eMatches.map((tag, j) => {
              const norm = tag.toUpperCase()
              return (
                <span key={norm}>
                  <CitationPill
                    id={norm}
                    onClick={onCitationClick}
                    highlighted={highlightedId === norm}
                  />
                  {j < eMatches.length - 1 ? ' ' : ''}
                </span>
              )
            })}
          </span>
        )
      }
    }
    return <span key={i}>{part}</span>
  })
}

function getGroundingState(grounded, answer) {
  if (!answer) return null
  const insufficient = answer.toLowerCase().includes('insufficient')
  if (insufficient) return 'insufficient'
  if (grounded) return 'grounded'
  return 'ungrounded'
}

function GroundingIndicator({ state }) {
  if (!state) return null
  const config = {
    grounded: {
      dot: '●',
      badge: 'GROUNDED',
      text: 'Evidence-backed synthesis',
    },
    ungrounded: {
      dot: '○',
      badge: 'UNVERIFIED',
      text: 'Model response not verified against evidence',
    },
    insufficient: {
      dot: '◐',
      badge: 'INSUFFICIENT EVIDENCE',
      text: 'Graph did not contain enough data',
    },
  }
  const { dot, badge, text } = config[state] || config.ungrounded
  return (
    <div className={`grounding-indicator ${state}`} role="status" aria-live="polite">
      <span className="grounding-dot" aria-hidden="true">{dot}</span>
      <span className="grounding-badge-tag">{badge}</span>
      <span className="grounding-sep" aria-hidden="true">·</span>
      <span className="grounding-text">{text}</span>
    </div>
  )
}

function EvidenceRows({ items, highlightedId, onHighlight, onNavigateToTrace }) {
  if (!items || items.length === 0) {
    return (
      <div className="empty-block" style={{ padding: '24px 20px' }}>
        <div className="empty-label">No Evidence Retrieved</div>
        <div className="empty-desc">No structural or semantic records matched this query in HydraDB.</div>
      </div>
    )
  }

  return (
    <div className="evidence-rows">
      {items.map((item) => (
        <div
          key={item.id}
          id={`evidence-${item.id}`}
          className={`evidence-row ${highlightedId === item.id ? 'highlighted' : ''}`}
          onClick={() => onHighlight(item.id === highlightedId ? null : item.id)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              onHighlight(item.id === highlightedId ? null : item.id)
            }
          }}
          aria-selected={highlightedId === item.id}
        >
          <div className="evidence-id" aria-label={`Evidence item ${item.id}`}>
            [{item.id}]
          </div>
          <div className="evidence-content">
            <div className="evidence-entity-row">
              {item.entity_name && (
                <span className="evidence-entity-name">{item.entity_name}</span>
              )}
              {item.statement_type && (
                <span className={`type-badge ${item.statement_type.toLowerCase()}`}>
                  {item.statement_type.toUpperCase()}
                </span>
              )}
              {item.relationship && (
                <span className="type-badge rel">{item.relationship}</span>
              )}
              {item.match_type && (
                <span className="match-tag">{item.match_type}</span>
              )}
              {item.entity_name && onNavigateToTrace && (
                <button
                  className="inline-trace-btn"
                  onClick={(e) => {
                    e.stopPropagation()
                    onNavigateToTrace(item.entity_name)
                  }}
                  title={`Trace dependencies for ${item.entity_name}`}
                  aria-label={`Trace dependencies for ${item.entity_name}`}
                  type="button"
                >
                  <span>TRACE</span>
                  <span aria-hidden="true">⟷</span>
                </button>
              )}
            </div>

            {item.statement ? (
              <div className="evidence-statement">{item.statement}</div>
            ) : (
              <div className="evidence-statement-empty">
                Direct graph reference without explicit statement text.
              </div>
            )}

            <div className="evidence-meta">
              {item.source && (
                <span className="source-tag">
                  <strong>src:</strong> {item.source}
                </span>
              )}
              {item.message_id ? (
                <span>
                  <strong>msg:</strong> {item.message_id}
                </span>
              ) : null}
              {item.document_id ? (
                <span>
                  <strong>doc:</strong>{' '}
                  <span title={item.document_id}>
                    {item.document_id.length > 22
                      ? `${item.document_id.slice(0, 22)}...`
                      : item.document_id}
                  </span>
                </span>
              ) : null}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function InvestigationView({
  initialQuery = '',
  onQueryChange,
  onNavigateToTrace,
}) {
  const [query, setQuery] = useState(initialQuery)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [highlightedId, setHighlightedId] = useState(null)
  const [latencyMs, setLatencyMs] = useState(null)
  const textareaRef = useRef(null)

  const suggestions = getInquiryQueries()

  const handleCitationClick = useCallback((id) => {
    setHighlightedId((prev) => (prev === id ? null : id))
    const el = document.getElementById(`evidence-${id}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [])

  const handleExecute = useCallback(async (queryOverride) => {
    const q = (queryOverride !== undefined ? queryOverride : query).trim()
    if (!q) return
    setLoading(true)
    setError(null)
    setResult(null)
    setHighlightedId(null)
    const t0 = performance.now()
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, retrieval_limit: 10 }),
      })
      const data = await res.json()
      const t1 = performance.now()
      setLatencyMs(Math.round(t1 - t0))
      if (!res.ok) {
        throw new Error(data.detail || data.error || `HTTP ${res.status}`)
      }
      setResult(data)
    } catch (err) {
      setError(err.message || 'Failed to query knowledge graph.')
    } finally {
      setLoading(false)
    }
  }, [query])

  // Handle external query navigation from Suggestions view
  useEffect(() => {
    if (initialQuery && initialQuery.trim() !== '') {
      setQuery(initialQuery)
      handleExecute(initialQuery)
    }
  }, [initialQuery, handleExecute])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleExecute()
    }
  }

  const handleSelectSuggestion = (sQuery) => {
    setQuery(sQuery)
    if (onQueryChange) onQueryChange(sQuery)
    handleExecute(sQuery)
  }

  const groundingState = result ? getGroundingState(result.grounded, result.answer) : null

  // Extract unique entities found in the evidence bundle
  const uniqueEntities = useMemo(() => {
    if (!result?.evidence) return []
    const names = new Set()
    for (const item of result.evidence) {
      if (item.entity_name) names.add(item.entity_name)
    }
    return Array.from(names)
  }, [result])

  return (
    <section aria-label="Investigation workspace" className="investigation-section">
      <div className="view-header">
        <h1 className="view-title">Investigate</h1>
        <div className="view-subtitle">
          Trace incident causes, architectural decisions, and verify evidence across HydraDB.
        </div>
      </div>

      {/* Query Console */}
      <div className="query-console" role="search">
        <div className="query-input-row">
          <div className="query-prefix" aria-hidden="true">&gt;_</div>
          <textarea
            ref={textareaRef}
            className="query-input"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              if (onQueryChange) onQueryChange(e.target.value)
            }}
            onKeyDown={handleKeyDown}
            placeholder="What happened during incident INC-2026? or What is PR-99501 about?"
            rows={2}
            aria-label="Investigation query input"
            disabled={loading}
          />
          <button
            className={`query-execute-btn ${loading ? 'loading' : ''}`}
            onClick={() => handleExecute()}
            disabled={loading || !query.trim()}
            aria-label="Execute query"
            type="button"
          >
            {loading ? (
              <>
                <span className="btn-spinner" aria-hidden="true" />
                <span>ANALYZING</span>
              </>
            ) : (
              <>
                <span className="btn-state-tag">READY</span>
                <span>EXECUTE →</span>
              </>
            )}
          </button>
        </div>

        {/* Command Suggestions */}
        <div className="query-suggestions" aria-label="Suggested investigations">
          <span className="suggestion-prefix">Suggested Inquiries:</span>
          <div className="suggestion-pills">
            {suggestions.map((s) => (
              <button
                key={s.label}
                className="suggestion-btn"
                onClick={() => handleSelectSuggestion(s.query)}
                aria-label={`Run investigation: ${s.label}`}
                type="button"
              >
                <span className="suggestion-icon" aria-hidden="true">&gt;_</span>
                <span>{s.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="state-block loading-state" role="status" aria-live="polite">
          <div className="loading-card">
            <div className="loading-spinner-ring" aria-hidden="true" />
            <div className="loading-content">
              <div className="loading-title">ANALYZING QUERY...</div>
              <div className="loading-desc">
                Traversing HydraDB graph relationships and assembling bounded evidence bundle
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="error-block" role="alert">
          <div className="error-label">Investigation Error</div>
          <div className="error-desc">{error}</div>
        </div>
      )}

      {/* Results Area */}
      {result && !loading && (
        <div className="result-area">
          {/* Query Bar */}
          <div className="query-meta-bar">
            <div className="query-meta-left">
              <span className="query-label-small">QUERY</span>
              <span className="query-text-display">&ldquo;{result.question}&rdquo;</span>
            </div>
            {latencyMs !== null && (
              <div className="query-latency-tag">
                <span className="latency-lbl">LATENCY</span>
                <span className="latency-val">{latencyMs} ms</span>
              </div>
            )}
          </div>

          {/* Insufficient Evidence Warning Banner if applicable */}
          {groundingState === 'insufficient' && (
            <div className="insufficient-alert" role="status">
              <div className="insufficient-alert-header">
                <span className="insufficient-icon" aria-hidden="true">◐</span>
                <strong>INSUFFICIENT EVIDENCE</strong>
              </div>
              <p className="insufficient-alert-body">
                HydraDB resolved partial graph entities, but the evidence bundle does not contain
                enough verified facts to answer the question conclusively without risking ungrounded extrapolation.
              </p>
            </div>
          )}

          {/* Synthesis Block */}
          <div className="synthesis-block">
            <div className="synthesis-header">
              <span className="synthesis-label">SYNTHESIS</span>
              <GroundingIndicator state={groundingState} />
            </div>
            <div className="synthesis-body">
              {formatAnswerWithCitations(
                result.answer,
                handleCitationClick,
                highlightedId
              )}
            </div>

            {/* Quick Entity Trace Shortcuts Row */}
            {uniqueEntities.length > 0 && onNavigateToTrace && (
              <div className="synthesis-entity-shortcuts">
                <span className="shortcuts-lbl">TRACE DISCOVERED ENTITIES:</span>
                <div className="shortcuts-list">
                  {uniqueEntities.map((ent) => (
                    <button
                      key={ent}
                      className="entity-shortcut-btn"
                      onClick={() => onNavigateToTrace(ent)}
                      title={`Trace dependencies for ${ent}`}
                      type="button"
                    >
                      <span className="shortcut-dot" aria-hidden="true">⟷</span>
                      <span>{ent}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Evidence Block */}
          <div className="evidence-block">
            <div className="evidence-header">
              <div className="evidence-header-left">
                <span className="evidence-header-label">EVIDENCE</span>
                <span className="evidence-count">
                  {result.evidence?.length ?? 0} item{result.evidence?.length === 1 ? '' : 's'} retrieved from HydraDB
                </span>
              </div>
              {highlightedId && (
                <button
                  className="evidence-clear-btn"
                  onClick={() => setHighlightedId(null)}
                  type="button"
                >
                  Clear Highlight [{highlightedId}]
                </button>
              )}
            </div>
            <EvidenceRows
              items={result.evidence}
              highlightedId={highlightedId}
              onHighlight={setHighlightedId}
              onNavigateToTrace={onNavigateToTrace}
            />
          </div>
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && !error && (
        <div className="empty-block starter-empty-block">
          <div className="starter-icon" aria-hidden="true">&gt;_</div>
          <div className="empty-label">INVESTIGATION CONSOLE</div>
          <div className="empty-desc">
            Ask Veridex about incidents, components, tickets, dependencies, or engineering decisions across the HydraDB graph.
          </div>
          <div className="starter-queries-row">
            <span className="starter-queries-label">Try an investigation query:</span>
            <div className="starter-buttons">
              {STARTER_QUERIES.map((sq) => (
                <button
                  key={sq}
                  className="starter-query-btn"
                  onClick={() => handleSelectSuggestion(sq)}
                  type="button"
                >
                  &ldquo;{sq}&rdquo;
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
