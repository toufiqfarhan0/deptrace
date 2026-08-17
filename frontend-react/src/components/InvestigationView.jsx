import React, { useState, useRef, useCallback } from 'react'

const SUGGESTIONS = [
  { label: 'REL-311 incident', query: 'What happened with REL-311?' },
  { label: 'model routing change', query: 'Why did the team change the model routing?' },
  { label: 'kernel-selector issue', query: 'What was the issue with kernel-selector?' },
  { label: 'strict_model:true', query: 'What is strict_model:true?' },
]

function CitationPill({ id, onClick, highlighted }) {
  return (
    <button
      className="citation-pill"
      onClick={() => onClick(id)}
      aria-label={`Jump to evidence ${id}`}
      style={highlighted ? { background: 'var(--c-accent)', color: '#000' } : undefined}
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
          <span key={i}>
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
    grounded: { dot: '●', text: 'GROUNDED · Evidence-backed synthesis' },
    ungrounded: { dot: '○', text: 'UNVERIFIED · Model response not verified against evidence' },
    insufficient: { dot: '◐', text: 'INSUFFICIENT EVIDENCE · Graph did not contain enough data' },
  }
  const { dot, text } = config[state] || config.ungrounded
  return (
    <div className={`grounding-indicator ${state}`} role="status" aria-live="polite">
      <span aria-hidden="true">{dot}</span>
      <span>{text}</span>
    </div>
  )
}

function EvidenceRows({ items, highlightedId, onHighlight }) {
  if (!items || items.length === 0) {
    return (
      <div className="empty-block" style={{ padding: '16px' }}>
        <div className="empty-label">No Evidence</div>
        <div className="empty-desc">No items retrieved from HydraDB for this query.</div>
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
            </div>
            {item.statement && (
              <div className="evidence-statement">{item.statement}</div>
            )}
            <div className="evidence-meta">
              {item.message_id ? <span><strong>msg:</strong> {item.message_id}</span> : null}
              {item.document_id ? (
                <span>
                  <strong>doc:</strong> {item.document_id.length > 25 ? `${item.document_id.slice(0, 25)}...` : item.document_id}
                </span>
              ) : null}
              {item.match_type ? <span><strong>match:</strong> {item.match_type}</span> : null}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function InvestigationView() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [highlightedId, setHighlightedId] = useState(null)
  const textareaRef = useRef(null)

  const handleCitationClick = useCallback((id) => {
    setHighlightedId((prev) => (prev === id ? null : id))
    const el = document.getElementById(`evidence-${id}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [])

  const handleExecute = useCallback(async () => {
    const q = query.trim()
    if (!q) return
    setLoading(true)
    setError(null)
    setResult(null)
    setHighlightedId(null)
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, retrieval_limit: 10 }),
      })
      const data = await res.json()
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

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleExecute()
    }
  }

  const groundingState = result ? getGroundingState(result.grounded, result.answer) : null

  return (
    <section aria-label="Investigation workspace">
      <div className="view-title">Investigate</div>
      <div className="view-subtitle">
        Trace incident causes, architectural decisions, and verify evidence across HydraDB.
      </div>

      {/* Query Console */}
      <div className="query-console" role="search">
        <div className="query-input-row">
          <div className="query-prefix" aria-hidden="true">&gt;_</div>
          <textarea
            ref={textareaRef}
            className="query-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="What happened with REL-311? or Why did the team change model routing?"
            rows={2}
            aria-label="Investigation query"
            disabled={loading}
          />
          <button
            className="query-execute-btn"
            onClick={handleExecute}
            disabled={loading || !query.trim()}
            aria-label="Execute query"
          >
            {loading ? '...' : 'EXECUTE →'}
          </button>
        </div>
        <div className="query-suggestions" aria-label="Query suggestions">
          <span className="suggestion-prefix">Suggested:</span>
          {SUGGESTIONS.map((s, i) => (
            <span key={s.label} style={{ display: 'flex', alignItems: 'center' }}>
              <button
                className="suggestion-btn"
                onClick={() => {
                  setQuery(s.query)
                  textareaRef.current?.focus()
                }}
                aria-label={`Use suggestion: ${s.label}`}
              >
                {s.label}
              </button>
              {i < SUGGESTIONS.length - 1 && <span className="suggestion-sep">·</span>}
            </span>
          ))}
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="state-block" role="status" aria-live="polite">
          <div className="loading-text">
            Querying HydraDB graph
            <div className="loading-dots" aria-hidden="true">
              <span/><span/><span/>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="error-block" role="alert">
          <div className="error-label">Investigation Error</div>
          <div className="error-desc">{error}</div>
        </div>
      )}

      {/* Result */}
      {result && !loading && (
        <div className="result-area">
          <div className="query-display">
            <div className="query-label-small">QUERY</div>
            <div className="query-text-display">&ldquo;{result.question}&rdquo;</div>
          </div>

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
          </div>

          <div className="evidence-block">
            <div className="evidence-header">
              <span className="evidence-header-label">EVIDENCE</span>
              <span className="evidence-count">
                {result.evidence?.length ?? 0} item{result.evidence?.length === 1 ? '' : 's'} retrieved from HydraDB
              </span>
            </div>
            <EvidenceRows
              items={result.evidence}
              highlightedId={highlightedId}
              onHighlight={setHighlightedId}
            />
          </div>
        </div>
      )}

      {/* Empty state */}
      {!result && !loading && !error && (
        <div className="empty-block">
          <div className="empty-label">Console Ready</div>
          <div className="empty-desc">
            Submit a query above or choose a suggested investigation prompt to retrieve deterministic
            graph facts, actions, and verified provenance.
          </div>
        </div>
      )}
    </section>
  )
}
