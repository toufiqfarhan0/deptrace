import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react'
import { getInquiryQueries } from '../data/suggestions.js'
import {
  consumeQuota,
  isRateLimitError,
  formatModelError,
  QUOTA_STUDENT_MESSAGE,
  RATE_LIMIT_MESSAGE,
  useQuota,
} from '../utils/quotaManager.js'

const STARTER_QUERIES = [
  'What happened during incident INC-2026?',
  'What is PR-99501 about?',
  'What is ENG-68910 about?',
  'What caused the Bluecrest gateway timeouts?',
]

function CitationPill({ id, onClick, highlighted }) {
  return (
    <button
      className={`citation-pill ${highlighted ? 'highlighted' : ''}`}
      onClick={(e) => {
        e.stopPropagation()
        if (onClick) onClick(id)
      }}
      aria-label={`Jump to evidence [${id}]`}
      type="button"
    >
      [{id}]
    </button>
  )
}

/**
 * Tokenizes inline text to parse citations [E1], bold **text**, inline code `code`,
 * and italic *text* into rich React components.
 */
function renderInlineWithCitations(text, onCitationClick, highlightedId) {
  if (!text) return null

  const tokens = []
  let remaining = text
  // Match citations e.g. [E1] or [E1, E2], bold **text**, inline code `code`, italic *text*
  const tokenRegex = /(\[[^\]]*E\d+[^\]]*\])|(\*\*[^*]+\*\*)|(`[^`]+`)|(\*[^*]+\*)/i
  let keyIdx = 0

  while (remaining) {
    const match = remaining.match(tokenRegex)
    if (!match) {
      tokens.push(
        React.createElement('span', { key: `txt-${keyIdx++}` }, remaining)
      )
      break
    }

    const matchIndex = match.index
    if (matchIndex > 0) {
      tokens.push(
        React.createElement(
          'span',
          { key: `txt-${keyIdx++}` },
          remaining.slice(0, matchIndex)
        )
      )
    }

    const matchedStr = match[0]

    // 1. Citation tag [E1] or grouped [E1, E2, E3]
    if (match[1]) {
      const eMatches = matchedStr.match(/E\d+/gi) || []
      const pills = eMatches.map((tag, j) => {
        const norm = tag.toUpperCase()
        const isHigh = highlightedId === norm
        return (
          <span key={`cit-${norm}-${keyIdx++}`}>
            <CitationPill
              id={norm}
              onClick={onCitationClick}
              highlighted={isHigh}
            />
            {j < eMatches.length - 1 ? ' ' : ''}
          </span>
        )
      })
      tokens.push(
        <span key={`cg-${keyIdx++}`} className="citation-group">
          {pills}
        </span>
      )
    }
    // 2. Bold **text**
    else if (match[2]) {
      const boldContent = matchedStr.slice(2, -2)
      tokens.push(
        <strong key={`b-${keyIdx++}`} className="md-strong">
          {renderInlineWithCitations(boldContent, onCitationClick, highlightedId)}
        </strong>
      )
    }
    // 3. Inline code `code`
    else if (match[3]) {
      const codeContent = matchedStr.slice(1, -1)
      tokens.push(
        <code key={`c-${keyIdx++}`} className="md-inline-code">
          {codeContent}
        </code>
      )
    }
    // 4. Italic *text*
    else if (match[4]) {
      const italicContent = matchedStr.slice(1, -1)
      tokens.push(
        <em key={`em-${keyIdx++}`} className="md-em">
          {renderInlineWithCitations(italicContent, onCitationClick, highlightedId)}
        </em>
      )
    }

    remaining = remaining.slice(matchIndex + matchedStr.length)
  }

  return tokens
}

/**
 * MarkdownAnswerRenderer renders formatted Gemini/RAG answers without exposing
 * raw markdown syntax (**, ###, bullets, code blocks), while keeping citation
 * pills interactive.
 */
function MarkdownAnswerRenderer({ answer, onCitationClick, highlightedId }) {
  if (!answer) return null

  const rawLines = answer.split(/\r?\n/)
  const blocks = []
  let currentList = null // { type: 'ul' | 'ol', items: [] }
  let currentCodeBlock = null // { lang: '', lines: [] }
  let blockIdx = 0

  function flushList() {
    if (currentList) {
      const isUl = currentList.type === 'ul'
      blocks.push(
        React.createElement(
          isUl ? 'ul' : 'ol',
          { key: `list-${blockIdx++}`, className: isUl ? 'md-ul' : 'md-ol' },
          currentList.items.map((it, i) => (
            <li key={`li-${i}`} className="md-li">
              {renderInlineWithCitations(it, onCitationClick, highlightedId)}
            </li>
          ))
        )
      )
      currentList = null
    }
  }

  for (let i = 0; i < rawLines.length; i++) {
    const line = rawLines[i]
    const trimmed = line.trim()

    // Fenced code block toggle
    if (trimmed.startsWith('```')) {
      if (currentCodeBlock) {
        blocks.push(
          <pre key={`codeblock-${blockIdx++}`} className="md-pre">
            <code className="md-code-block">{currentCodeBlock.lines.join('\n')}</code>
          </pre>
        )
        currentCodeBlock = null
      } else {
        flushList()
        currentCodeBlock = { lang: trimmed.slice(3).trim(), lines: [] }
      }
      continue
    }

    if (currentCodeBlock) {
      currentCodeBlock.lines.push(line)
      continue
    }

    if (!trimmed) {
      flushList()
      continue
    }

    // Headings: ###, ##, #
    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/)
    if (headingMatch) {
      flushList()
      const level = headingMatch[1].length
      const headingText = headingMatch[2]
      const Tag = level === 1 ? 'h2' : level === 2 ? 'h3' : 'h4'
      blocks.push(
        React.createElement(
          Tag,
          { key: `h-${blockIdx++}`, className: `md-heading md-h${level}` },
          renderInlineWithCitations(headingText, onCitationClick, highlightedId)
        )
      )
      continue
    }

    // Unordered list item: - item, * item, • item
    const ulMatch = trimmed.match(/^[-*•]\s+(.+)$/)
    if (ulMatch) {
      if (!currentList || currentList.type !== 'ul') {
        flushList()
        currentList = { type: 'ul', items: [] }
      }
      currentList.items.push(ulMatch[1])
      continue
    }

    // Ordered list item: 1. item
    const olMatch = trimmed.match(/^\d+\.\s+(.+)$/)
    if (olMatch) {
      if (!currentList || currentList.type !== 'ol') {
        flushList()
        currentList = { type: 'ol', items: [] }
      }
      currentList.items.push(olMatch[1])
      continue
    }

    // Regular paragraph
    flushList()
    blocks.push(
      <p key={`p-${blockIdx++}`} className="md-paragraph">
        {renderInlineWithCitations(trimmed, onCitationClick, highlightedId)}
      </p>
    )
  }

  flushList()

  return <div className="md-rendered-answer">{blocks}</div>
}

function getGroundingState(grounded, answer) {
  if (!answer) return null
  const insufficient = answer.toLowerCase().includes('insufficient')
  if (insufficient) return 'insufficient'
  if (grounded) return 'grounded'
  return 'ungrounded'
}

function GroundingStatusChip({ state, evidenceCount }) {
  if (!state) return null
  const isGrounded = state === 'grounded'
  const isInsufficient = state === 'insufficient'

  return (
    <div className={`synthesis-status-chip ${state}`} role="status" aria-live="polite">
      <span
        className={`status-dot ${isGrounded ? 'ok' : isInsufficient ? 'warning' : 'neutral'}`}
        aria-hidden="true"
      />
      <span className="status-chip-label">
        {isGrounded
          ? `Grounded in HydraDB evidence · ${evidenceCount ?? 0} sources`
          : isInsufficient
          ? 'Insufficient evidence in graph'
          : 'Unverified response'}
      </span>
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
                  <strong>Source:</strong> {item.source}
                </span>
              )}
              {item.message_id ? (
                <span>
                  <strong>Message ID:</strong> {item.message_id}
                </span>
              ) : null}
              {item.document_id ? (
                <span>
                  <strong>Document:</strong>{' '}
                  <span title={item.document_id}>
                    {item.document_id.length > 24
                      ? `${item.document_id.slice(0, 24)}...`
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
  isActive = true,
}) {
  const [query, setQuery] = useState(initialQuery)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [highlightedId, setHighlightedId] = useState(null)
  const [latencyMs, setLatencyMs] = useState(null)
  const textareaRef = useRef(null)
  const quota = useQuota()

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

    // Enforce 3-interaction quota limit
    const quotaCheck = consumeQuota()
    if (!quotaCheck.allowed) {
      setError(QUOTA_STUDENT_MESSAGE)
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)
    setHighlightedId(null)
    // Clear the input text upon asking so the search bar is clean for next question
    setQuery('')
    if (onQueryChange) onQueryChange('')
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
      if (data.error && isRateLimitError(data.error)) {
        data.answer = RATE_LIMIT_MESSAGE
      }
      if (data.answer && isRateLimitError(data.answer)) {
        data.answer = RATE_LIMIT_MESSAGE
      }
      setResult(data)
    } catch (err) {
      if (isRateLimitError(err.message)) {
        setError(RATE_LIMIT_MESSAGE)
      } else {
        setError(err.message || 'Failed to query knowledge graph.')
      }
    } finally {
      setLoading(false)
    }
  }, [query, onQueryChange])

  // Sync draft query from external navigation WITHOUT auto-executing
  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery)
    }
  }, [initialQuery])

  // Clear unsubmitted draft text when user navigates away to trace or entity
  useEffect(() => {
    if (!isActive && query && !loading) {
      setQuery('')
      if (onQueryChange) onQueryChange('')
    }
  }, [isActive, query, loading, onQueryChange])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleExecute()
    }
  }


  const handleSelectSuggestion = (sQuery) => {
    setQuery(sQuery)
    if (onQueryChange) onQueryChange(sQuery)
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
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

  const extractedEntityCandidate = useMemo(() => {
    if (uniqueEntities && uniqueEntities.length > 0) return uniqueEntities[0]
    if (result?.question) {
      const match = result.question.match(/(PR-\d+|INC-\d+|REL-\d+|ENG-\d+|DES-\d+|kernel-selector|api-search|v3.1.1-legacy-tokenizer)/i)
      if (match) return match[0]
    }
    return ''
  }, [uniqueEntities, result])

  return (
    <section aria-label="Investigation workspace" className="investigation-section">
      <div className="view-header">
        <h1 className="view-title">Investigate</h1>
        <div className="view-subtitle">
          Ask questions about incidents, tickets, pull requests, and engineering decisions grounded in HydraDB.
        </div>
      </div>

      {/* Student Quota Exceeded Banner */}
      {quota.isExceeded && (
        <div className="quota-student-banner" role="alert">
          <span className="quota-student-icon" aria-hidden="true">⚠️</span>
          <span className="quota-student-text">{QUOTA_STUDENT_MESSAGE}</span>
        </div>
      )}

      {/* Query Input Card */}
      <div className="query-console" role="search">
        <div className="query-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label htmlFor="investigation-input" className="query-card-label">
            What would you like to investigate?
          </label>
          <div className={`quota-status-tag ${quota.isExceeded ? 'exceeded' : ''}`} title="Demo Quota: max 3 interactions">
            <span>Quota:</span>
            <strong>{quota.remaining} / {quota.maxQuota} remaining</strong>
          </div>
        </div>
        <div className="query-input-row">
          <textarea
            id="investigation-input"
            ref={textareaRef}
            className="query-input"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              if (onQueryChange) onQueryChange(e.target.value)
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask about incidents, tickets, pull requests, dependencies, or engineering decisions..."
            rows={2}
            aria-label="Investigation query input"
            disabled={loading}
          />
          <button
            className={`query-execute-btn ${loading ? 'loading' : ''}`}
            onClick={() => handleExecute()}
            disabled={loading || !query.trim()}
            aria-label="Ask Veridex"
            type="button"
          >
            {loading ? (
              <>
                <span className="btn-spinner" aria-hidden="true" />
                <span>SEARCHING...</span>
              </>
            ) : (
              <>
                <span>ASK VERIDEX</span>
                <span aria-hidden="true">→</span>
              </>
            )}
          </button>
        </div>

        {/* Suggestion Chips */}
        <div className="query-suggestions" aria-label="Suggested investigations">
          <span className="suggestion-prefix">Try asking:</span>
          <div className="suggestion-pills">
            {suggestions.map((s) => (
              <button
                key={s.label}
                className="suggestion-btn"
                onClick={() => handleSelectSuggestion(s.query)}
                aria-label={`Fill question: ${s.label}`}
                type="button"
              >
                <span>{s.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading Skeleton Wireframe State */}
      {loading && (
        <div className="skeleton-result-area" role="status" aria-live="polite" aria-label="Traversing knowledge graph">
          <div className="skeleton-meta-bar shimmer" />
          <div className="skeleton-synthesis-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div className="skeleton-badge shimmer" />
              <div className="skeleton-badge shimmer" style={{ width: '180px' }} />
            </div>
            <div className="skeleton-line shimmer" style={{ width: '96%', height: '14px' }} />
            <div className="skeleton-line shimmer" style={{ width: '91%', height: '14px' }} />
            <div className="skeleton-line shimmer" style={{ width: '74%', height: '14px' }} />
          </div>
          <div className="skeleton-evidence-list">
            <div className="skeleton-row shimmer" />
            <div className="skeleton-row shimmer" />
            <div className="skeleton-row shimmer" />
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className={`error-block ${error === QUOTA_STUDENT_MESSAGE ? 'quota-exceeded-block' : ''}`} role="alert">
          <div className="error-label">
            {error === QUOTA_STUDENT_MESSAGE
              ? 'DEMO QUOTA LIMIT REACHED'
              : isRateLimitError(error)
              ? 'MODEL LIMIT REACHED'
              : 'Investigation Error'}
          </div>
          <div className="error-desc">{formatModelError(error, error)}</div>
        </div>
      )}

      {/* Results Area */}
      {result && !loading && (
        <div className="result-area">
          {/* Query Bar */}
          <div className="query-meta-bar">
            <div className="query-meta-left">
              <span className="query-label-small">QUESTION</span>
              <span className="query-text-display">&ldquo;{result.question}&rdquo;</span>
            </div>
            {latencyMs !== null && (
              <div className="query-latency-tag">
                <span className="latency-lbl">LATENCY</span>
                <span className="latency-val">{latencyMs} ms</span>
              </div>
            )}
          </div>

          {/* Insufficient Evidence Explanation & Fallback Actions */}
          {groundingState === 'insufficient' && (
            <div className="insufficient-alert" role="status">
              <div className="insufficient-alert-header">
                <span className="insufficient-icon" aria-hidden="true">◐</span>
                <strong>Not enough evidence to answer this question</strong>
              </div>
              <p className="insufficient-alert-body">
                HydraDB found this entity and its relationships, but the available source material does not contain enough supporting text for a grounded answer.
              </p>
              <div className="insufficient-actions">
                {extractedEntityCandidate && onNavigateToTrace && (
                  <button
                    className="insufficient-fallback-btn trace-fallback"
                    onClick={() => onNavigateToTrace(extractedEntityCandidate)}
                    title={`Trace relationships for ${extractedEntityCandidate}`}
                    type="button"
                  >
                    <span>TRACE THIS ENTITY ({extractedEntityCandidate})</span>
                    <span aria-hidden="true">→</span>
                  </button>
                )}
                <button
                  className="insufficient-fallback-btn ask-fallback"
                  onClick={() => {
                    setQuery('')
                    if (onQueryChange) onQueryChange('')
                    if (textareaRef.current) textareaRef.current.focus()
                  }}
                  type="button"
                >
                  <span>TRY ANOTHER QUESTION</span>
                </button>
              </div>
            </div>
          )}

          {/* Answer Block */}
          <div className="synthesis-block">
            <div className="synthesis-header">
              <div className="synthesis-header-main">
                <span className="synthesis-title">INVESTIGATION RESULT</span>
              </div>
              <GroundingStatusChip state={groundingState} evidenceCount={result.evidence?.length ?? 0} />
            </div>
            <div className="synthesis-body">
              <MarkdownAnswerRenderer
                answer={result.answer}
                onCitationClick={handleCitationClick}
                highlightedId={highlightedId}
              />
            </div>

            {/* Quick Entity Trace Shortcuts Row */}
            {uniqueEntities.length > 0 && onNavigateToTrace && (
              <div className="synthesis-entity-shortcuts">
                <div className="shortcuts-header">
                  <span className="shortcuts-icon" aria-hidden="true">⟷</span>
                  <span className="shortcuts-lbl">RELATED GRAPH ENTITIES · INVESTIGATE NEXT</span>
                </div>
                <div className="shortcuts-list">
                  {uniqueEntities.map((ent) => (
                    <div key={ent} className="entity-chip-card">
                      <span className="entity-chip-name">{ent}</span>
                      <div className="entity-chip-actions">
                        <button
                          className="entity-chip-action-btn"
                          onClick={() => onNavigateToTrace(ent)}
                          title={`Trace dependency connections for ${ent}`}
                          type="button"
                        >
                          <span>Trace Connections</span>
                          <span aria-hidden="true">⟷</span>
                        </button>
                        <button
                          className="entity-chip-action-btn secondary"
                          onClick={() => {
                            const q = `What is ${ent} about?`
                            setQuery(q)
                            if (onQueryChange) onQueryChange(q)
                            if (textareaRef.current) textareaRef.current.focus()
                          }}
                          title={`Ask a question about ${ent}`}
                          type="button"
                        >
                          <span>Ask about this</span>
                          <span aria-hidden="true">→</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Evidence Block */}
          <div className="evidence-block">
            <div className="evidence-header">
              <div className="evidence-header-left">
                <span className="evidence-header-label">EVIDENCE FROM HYDRADB</span>
                <span className="evidence-count">
                  {result.evidence?.length ?? 0} verified source{result.evidence?.length === 1 ? '' : 's'} retrieved from knowledge graph
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

      {/* Empty Starter State */}
      {!result && !loading && !error && (
        <div className="empty-block starter-empty-block">
          <div className="starter-header">
            <div className="empty-label">START AN INVESTIGATION</div>
            <div className="empty-desc">
              Ask questions about incidents, pull requests, Linear tickets, or Slack discussions.
              Veridex deterministically queries the HydraDB knowledge graph to retrieve verified facts and synthesizes grounded answers with citations.
            </div>
          </div>
          <div className="starter-queries-row">
            <span className="starter-queries-label">Click an example question to populate:</span>
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
