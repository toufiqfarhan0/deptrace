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
    <section aria-label="Entity explorer" className="entities-section">
      <div className="view-header">
        <h1 className="view-title">Explore Engineering Entities</h1>
        <div className="view-subtitle">
          Browse entities discovered in the HydraDB knowledge graph. Investigate their context or trace their dependency network.
        </div>
      </div>

      <div className="entity-filter-row" role="search">
        <input
          className="entity-filter-input"
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter entities by name (e.g. PR-99501, INC-2026, tokenizer, api-search)..."
          aria-label="Filter entities"
        />
        {filter && (
          <button
            className="search-clear-btn"
            onClick={() => setFilter('')}
            aria-label="Clear filter"
            type="button"
          >
            ✕
          </button>
        )}
      </div>

      {loading ? (
        <div className="state-block loading-state" role="status">
          <div className="loading-card">
            <div className="loading-spinner-ring" aria-hidden="true" />
            <div className="loading-content">
              <div className="loading-title">LOADING ENTITIES</div>
              <div className="loading-desc">Fetching graph entities from HydraDB...</div>
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
            Showing <strong>{filtered.length}</strong> of {entities.length} entities in graph
          </div>
          {filtered.length > 0 ? (
            <div className="entity-list">
              {filtered.map((entity) => (
                <div
                  key={entity}
                  className="entity-row"
                  aria-label={`Entity ${entity}`}
                >
                  <span className="entity-name">{entity}</span>
                  <div className="entity-row-actions">
                    {onAskEntity && (
                      <button
                        className="entity-action-btn entity-ask-btn"
                        onClick={() => onAskEntity(`What is connected to ${entity}?`)}
                        title={`Ask question about ${entity}`}
                        aria-label={`Ask about ${entity}`}
                        type="button"
                      >
                        <span>ASK ABOUT THIS</span>
                        <span aria-hidden="true">→</span>
                      </button>
                    )}
                    <button
                      className="entity-action-btn entity-trace-btn"
                      onClick={() => onTraceEntity(entity)}
                      title={`Trace dependencies for ${entity}`}
                      aria-label={`Trace dependencies for ${entity}`}
                      type="button"
                    >
                      <span>TRACE THIS</span>
                      <span aria-hidden="true">⟷</span>
                    </button>
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
