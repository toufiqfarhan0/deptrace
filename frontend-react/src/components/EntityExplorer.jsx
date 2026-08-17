import React, { useState, useEffect } from 'react'

export default function EntityExplorer({ onTraceEntity, onAskEntity }) {
  const [entities, setEntities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/trace/entities')
        const data = await res.json()
        setEntities(data.entities || [])
      } catch (err) {
        setError('Failed to load entities from HydraDB.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const filtered = entities.filter((e) =>
    e.toLowerCase().includes(filter.toLowerCase().trim())
  )

  return (
    <section aria-label="Entity explorer">
      <div className="view-title">Entities</div>
      <div className="view-subtitle">
        All unique entities identified across the HydraDB knowledge graph. Trace dependencies or investigate incidents.
      </div>

      <div className="entity-filter-row">
        <input
          className="entity-filter-input"
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter entities (e.g. REL-311, kernel, tokenizer, api-search)..."
          aria-label="Filter entities"
        />
      </div>

      {loading ? (
        <div className="state-block" role="status">
          <div className="loading-text">
            Loading entities from graph
            <div className="loading-dots" aria-hidden="true">
              <span/><span/><span/>
            </div>
          </div>
        </div>
      ) : error ? (
        <div className="error-block" role="alert">
          <div className="error-label">Error</div>
          <div className="error-desc">{error}</div>
        </div>
      ) : (
        <>
          <div className="entity-count-line">
            Showing {filtered.length} of {entities.length} entities in graph
          </div>
          {filtered.length > 0 ? (
            <div className="entity-list">
              {filtered.map((entity) => (
                <div
                  key={entity}
                  className="entity-row"
                  onClick={() => onTraceEntity(entity)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      onTraceEntity(entity)
                    }
                  }}
                  aria-label={`Trace dependencies for ${entity}`}
                >
                  <span className="entity-name">{entity}</span>
                  <div className="entity-row-actions">
                    {onAskEntity && (
                      <button
                        className="inline-ask-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          onAskEntity(`What is connected to ${entity}?`)
                        }}
                        title={`Ask question about ${entity}`}
                        aria-label={`Ask about ${entity}`}
                        type="button"
                      >
                        <span>&gt;_ ASK</span>
                      </button>
                    )}
                    <span className="entity-trace-hint" aria-hidden="true">trace →</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-block">
              <div className="empty-label">No Matching Entities</div>
              <div className="empty-desc">No entities match &ldquo;{filter}&rdquo;</div>
            </div>
          )}
        </>
      )}
    </section>
  )
}
