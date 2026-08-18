import React, { useState, useEffect } from 'react'

function getEntityType(name) {
  if (!name) return 'Entity'
  const u = name.toUpperCase()
  if (u.startsWith('PR-') || u.startsWith('PR#')) return 'GitHub Pull Request'
  if (u.startsWith('INC-')) return 'Incident'
  if (u.startsWith('REL-')) return 'Support Ticket / Release'
  if (u.startsWith('ENG-') || u.startsWith('PAY-') || u.startsWith('DES-')) return 'Issue / Ticket'
  if (name.includes(':') || name.includes('model') || name.includes('setting')) return 'Configuration Setting'
  if (name.includes('guard') || name.includes('policy')) return 'Guardrail / Policy'
  return 'Component'
}

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
    <section aria-label="Explore engineering knowledge" className="entities-section">
      <div className="view-header">
        <h1 className="view-title">Explore engineering knowledge</h1>
        <div className="view-subtitle">
          Browse incidents, tickets, pull requests, components, and other entities discovered in the HydraDB knowledge graph.
        </div>
      </div>

      <div className="entity-filter-row" role="search">
        <input
          className="entity-filter-input"
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Search discovered entities (e.g. PR-99501, INC-2026, tokenizer, api-search)..."
          aria-label="Search entities"
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
              <div className="loading-title">LOADING DISCOVERED ENTITIES</div>
              <div className="loading-desc">Fetching graph objects from HydraDB...</div>
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
            <span>
              <strong>{filtered.length}</strong> entities discovered in HydraDB graph
            </span>
          </div>

          {filtered.length > 0 ? (
            <div className="entity-cards-grid">
              {filtered.map((entity) => {
                const typeLabel = getEntityType(entity)
                return (
                  <div
                    key={entity}
                    className="entity-card"
                    aria-label={`Entity ${entity}`}
                  >
                    <div className="entity-card-top">
                      <div className="entity-card-header">
                        <span className="entity-card-name">{entity}</span>
                        <span className="entity-type-badge">{typeLabel}</span>
                      </div>
                      <div className="entity-availability-badge">
                        <span className="availability-dot" aria-hidden="true">◈</span>
                        <span>Graph relationships available</span>
                      </div>
                    </div>

                    <div className="entity-card-actions">
                      {onAskEntity && (
                        <div className="entity-action-wrapper">
                          <button
                            className="entity-action-btn entity-ask-btn"
                            onClick={() => onAskEntity(`What is ${entity} about?`)}
                            title={`Ask question about ${entity}`}
                            aria-label={`Ask about ${entity}`}
                            type="button"
                          >
                            <span>ASK ABOUT THIS</span>
                            <span aria-hidden="true">→</span>
                          </button>
                          <span className="entity-action-subtext">
                            Get an evidence-backed answer when supporting source text is available.
                          </span>
                        </div>
                      )}

                      <div className="entity-action-wrapper">
                        <button
                          className="entity-action-btn entity-trace-btn"
                          onClick={() => onTraceEntity(entity)}
                          title={`Trace connections for ${entity}`}
                          aria-label={`Trace connections for ${entity}`}
                          type="button"
                        >
                          <span>TRACE CONNECTIONS</span>
                          <span aria-hidden="true">⟷</span>
                        </button>
                        <span className="entity-action-subtext">
                          Explore how this entity connects to other incidents, tickets, pull requests, and components.
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
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
