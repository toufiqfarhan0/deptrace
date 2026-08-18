import React, { useState, useEffect } from 'react'

function getEntityMeta(entity) {
  const norm = entity.trim()

  // Entity Type Determination
  let type = 'Knowledge Graph Object'
  if (norm.startsWith('PR-')) type = 'GitHub Pull Request'
  else if (norm.startsWith('INC-')) type = 'Incident'
  else if (norm.startsWith('REL-')) type = 'Support Ticket / Incident'
  else if (norm.startsWith('ENG-')) type = 'Issue / Ticket'
  else if (norm.startsWith('DES-')) type = 'Design Spec'
  else if (['kernel-selector', 'api-search', 'v3.1.1-legacy-tokenizer', 'request-time guard', 'Bluecrest'].includes(norm)) type = 'Component'
  else if (norm.includes(':') || norm.includes('model')) type = 'Configuration Tag'

  // Evidence availability determination safely without guessing
  // Known evidence entities in HydraDB frozen dataset vs pure structural graph nodes
  const textEvidenceEntities = [
    'PR-99501',
    'REL-311',
    'INC-2026',
    'ENG-68910',
    'ENG-233901',
    'ENG-30521',
    'kernel-selector',
    'api-search',
    'v3.1.1-legacy-tokenizer',
    'request-time guard',
    'DES-23981',
    'PR-482199',
    'PR-209876',
    'Bluecrest',
  ]

  const isStructuralOnly = ['strict_model:true', 'compact-model-v1'].includes(norm)
  const hasTextEvidence = textEvidenceEntities.includes(norm)

  let evidenceBadge = null
  if (hasTextEvidence) {
    evidenceBadge = { label: 'Evidence available', type: 'evidence-available' }
  } else if (isStructuralOnly) {
    evidenceBadge = { label: 'Graph relationships available', type: 'graph-available' }
  }

  // Generate clear default ask query
  let askQuery = `What is ${norm} about?`
  if (type === 'Incident') askQuery = `What happened during incident ${norm}?`
  else if (type === 'Support Ticket / Incident') askQuery = `What happened with ${norm}?`
  else if (type === 'GitHub Pull Request') askQuery = `What changes were made in ${norm}?`

  return { type, evidenceBadge, askQuery }
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
    <section aria-label="Entity explorer" className="entities-section">
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
          placeholder="Search entities by name (e.g. PR-99501, INC-2026, kernel-selector, api-search)..."
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
            Showing <strong>{filtered.length}</strong> of {entities.length} entities in HydraDB knowledge graph
          </div>
          {filtered.length > 0 ? (
            <div className="entity-cards-grid">
              {filtered.map((entity) => {
                const meta = getEntityMeta(entity)
                return (
                  <div
                    key={entity}
                    className="entity-card"
                    aria-label={`Entity ${entity}`}
                  >
                    <div className="entity-card-header">
                      <div className="entity-header-top">
                        <span className="entity-card-name">{entity}</span>
                        {meta.evidenceBadge && (
                          <span className={`entity-evidence-badge ${meta.evidenceBadge.type}`}>
                            {meta.evidenceBadge.label}
                          </span>
                        )}
                      </div>
                      <div className="entity-kind-tag">{meta.type}</div>
                    </div>

                    <div className="entity-card-actions">
                      {onAskEntity && (
                        <button
                          className="entity-card-btn entity-ask-btn"
                          onClick={() => onAskEntity(meta.askQuery)}
                          title="Get an evidence-backed answer when supporting source text is available."
                          aria-label={`Ask about ${entity}`}
                          type="button"
                        >
                          <div className="btn-main-label">
                            <span>ASK ABOUT THIS</span>
                            <span aria-hidden="true">→</span>
                          </div>
                          <div className="btn-sub-label">
                            Get an evidence-backed answer when supporting source text is available.
                          </div>
                        </button>
                      )}
                      {onTraceEntity && (
                        <button
                          className="entity-card-btn entity-trace-btn"
                          onClick={() => onTraceEntity(entity)}
                          title="Explore how this entity connects to other incidents, tickets, pull requests, and components."
                          aria-label={`Trace connections for ${entity}`}
                          type="button"
                        >
                          <div className="btn-main-label">
                            <span>TRACE CONNECTIONS</span>
                            <span aria-hidden="true">⟷</span>
                          </div>
                          <div className="btn-sub-label">
                            Explore how this entity connects to other incidents, tickets, pull requests, and components.
                          </div>
                        </button>
                      )}
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
