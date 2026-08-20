import React, { useState, useEffect } from 'react'
import {
  isRateLimitError,
  formatModelError,
  QUOTA_STUDENT_MESSAGE,
  RATE_LIMIT_MESSAGE,
  useQuota,
} from '../utils/quotaManager.js'

function getEntityMeta(entity) {
  const norm = entity.trim()

  // Entity Type Determination
  let type = 'Knowledge Graph Object'
  if (norm.startsWith('PR-')) type = 'GitHub Pull Request'
  else if (norm.startsWith('INC-')) type = 'Incident'
  else if (norm.startsWith('REL-')) type = 'Support Ticket / Incident'
  else if (norm.startsWith('ENG-')) type = 'Linear Issue / Ticket'
  else if (norm.startsWith('DES-')) type = 'Design Spec'
  else if (norm.startsWith('PM-')) type = 'Product Spec / Project'
  else if (['kernel-selector', 'api-search', 'v3.1.1-legacy-tokenizer', 'request-time guard', 'Bluecrest', 'kernel-fallback policy'].includes(norm)) type = 'Component / Service'
  else if (norm.includes(':') || norm.includes('model')) type = 'Configuration Parameter'

  // Evidence availability determination safely without guessing
  // Known evidence entities in HydraDB frozen dataset vs pure structural graph nodes
  const textEvidenceEntities = [
    'PR-99501',
    'PR-993211',
    'PR-482199',
    'PR-209876',
    'PR-947999',
    'PR-35802',
    'PR-91234',
    'REL-311',
    'INC-2026',
    'ENG-68910',
    'ENG-233901',
    'ENG-30521',
    'ENG-762314',
    'ENG-5432',
    'DES-23981',
    'PM-352917',
    'PM-16842',
    'Bluecrest',
    'kernel-selector',
    'api-search',
    'v3.1.1-legacy-tokenizer',
    'request-time guard',
    'kernel-fallback policy',
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
  else if (type === 'Linear Issue / Ticket') askQuery = `What is ticket ${norm} about?`

  return { type, evidenceBadge, askQuery }
}

export default function EntityExplorer({ onTraceEntity, onAskEntity }) {
  const [entities, setEntities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('')
  const quota = useQuota()

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/api/trace/entities')
        const data = await res.json()
        setEntities(data.entities || [])
      } catch (err) {
        if (isRateLimitError(err?.message)) {
          setError(RATE_LIMIT_MESSAGE)
        } else {
          setError('Failed to load entities from HydraDB.')
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleAskClick = (askQuery) => {
    if (quota.isExceeded) {
      setError(quota.studentMessage)
      return
    }
    if (onAskEntity) onAskEntity(askQuery)
  }

  const handleTraceClick = (entityName) => {
    if (quota.isExceeded) {
      setError(quota.studentMessage)
      return
    }
    if (onTraceEntity) onTraceEntity(entityName)
  }

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

      {/* Progressive Quota Exceeded Banner */}
      {quota.isExceeded && (
        <div className="quota-student-banner" role="alert">
          <span className="quota-student-icon" aria-hidden="true">💡</span>
          <span className="quota-student-text">{quota.studentMessage}</span>
        </div>
      )}

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
        <div className={`error-block ${quota.isExceeded || error === quota.studentMessage ? 'quota-exceeded-block' : ''}`} role="alert">
          <div className="error-label">
            {quota.isExceeded || error === quota.studentMessage
              ? 'DEMO QUOTA LIMIT REACHED'
              : isRateLimitError(error)
              ? 'MODEL LIMIT REACHED'
              : 'Error'}
          </div>
          <div className="error-desc">{formatModelError(error, error)}</div>
        </div>
      ) : (
        <>
          <div className="entity-count-line" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>
              Showing <strong>{filtered.length}</strong> of {entities.length} entities in HydraDB knowledge graph
            </span>
            <div className={`quota-status-tag ${quota.isExceeded ? 'exceeded' : ''}`} title="Demo Quota">
              <span>Quota:</span>
              <strong>{quota.remaining} / {quota.maxQuota} remaining</strong>
            </div>
          </div>
          {filtered.length > 0 ? (
            <div className="entity-list-table-container">
              <table className="entity-list-table" aria-label="HydraDB Entities List">
                <thead>
                  <tr>
                    <th scope="col">ENTITY / IDENTIFIER</th>
                    <th scope="col">CLASSIFICATION</th>
                    <th scope="col">GRAPH EVIDENCE STATUS</th>
                    <th scope="col" style={{ textAlign: 'right' }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((entity) => {
                    const meta = getEntityMeta(entity)
                    return (
                      <tr key={entity} className="entity-list-row">
                        <td className="entity-col-name">
                          <span className="entity-list-name">{entity}</span>
                        </td>
                        <td className="entity-col-kind">
                          <span className="entity-list-kind">{meta.type}</span>
                        </td>
                        <td className="entity-col-status">
                          {meta.evidenceBadge ? (
                            <span className={`entity-evidence-badge ${meta.evidenceBadge.type}`}>
                              {meta.evidenceBadge.label}
                            </span>
                          ) : (
                            <span className="entity-evidence-badge graph-available">
                              Graph Node
                            </span>
                          )}
                        </td>
                        <td className="entity-col-actions">
                          <div className="entity-actions-inline">
                            {onAskEntity && (
                              <button
                                className="entity-action-btn ask-btn"
                                onClick={() => handleAskClick(meta.askQuery)}
                                title={`Ask a question about ${entity}`}
                                aria-label={`Ask about ${entity}`}
                                type="button"
                              >
                                <span>ASK</span>
                                <span aria-hidden="true">→</span>
                              </button>
                            )}
                            {onTraceEntity && (
                              <button
                                className="entity-action-btn trace-btn"
                                onClick={() => handleTraceClick(entity)}
                                title={`Trace dependency connections for ${entity}`}
                                aria-label={`Trace connections for ${entity}`}
                                type="button"
                              >
                                <span>TRACE</span>
                                <span aria-hidden="true">⟷</span>
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
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
