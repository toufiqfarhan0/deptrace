import React, { useState, useMemo } from 'react'
import {
  DATASET_STATS,
  SUGGESTIONS_CATALOG,
  getFilteredSuggestions,
} from '../data/suggestions.js'
import {
  QUOTA_STUDENT_MESSAGE,
  useQuota,
} from '../utils/quotaManager.js'

const CATEGORIES = [
  { id: 'ALL', label: 'All' },
  { id: 'INCIDENTS', label: 'Incidents' },
  { id: 'ENTITIES', label: 'Entities' },
  { id: 'LINEAR', label: 'Linear' },
  { id: 'GITHUB', label: 'GitHub' },
  { id: 'SLACK', label: 'Slack' },
  { id: 'CROSS-SOURCE', label: 'Cross-Source' },
]

export default function SuggestionsView({ onSelectQuery, onSelectTrace }) {
  const [category, setCategory] = useState('ALL')
  const [search, setSearch] = useState('')
  const [error, setError] = useState(null)
  const quota = useQuota()

  const filtered = useMemo(() => {
    return getFilteredSuggestions(category, search)
  }, [category, search])

  const handleTagClick = (tag) => {
    setSearch(tag)
  }

  const handleClearFilters = () => {
    setCategory('ALL')
    setSearch('')
  }

  const handleQueryClick = (q) => {
    if (quota.isExceeded) {
      setError(QUOTA_STUDENT_MESSAGE)
      return
    }
    onSelectQuery(q)
  }

  const handleTraceClick = (e) => {
    if (quota.isExceeded) {
      setError(QUOTA_STUDENT_MESSAGE)
      return
    }
    onSelectTrace(e)
  }

  return (
    <section aria-label="Investigation suggestions catalog" className="suggestions-section">
      <div className="view-header">
        <h1 className="view-title">Start with a Real Investigation</h1>
        <div className="view-subtitle">
          Explore verified questions from the HydraDB demo knowledge graph spanning Slack, Linear, and GitHub.
        </div>
      </div>

      {/* Student Quota Exceeded Banner */}
      {(quota.isExceeded || error) && (
        <div className="quota-student-banner" role="alert">
          <span className="quota-student-icon" aria-hidden="true">⚠️</span>
          <span className="quota-student-text">{QUOTA_STUDENT_MESSAGE}</span>
        </div>
      )}

      {/* Dataset Freeze Context Banner */}
      <div className="dataset-context-banner" role="region" aria-label="Dataset status">
        <div className="dataset-context-left">
          <span className="dataset-status-dot" aria-hidden="true" />
          <span className="dataset-context-tag">FROZEN DEMO DATASET</span>
          <span className="dataset-context-sep" aria-hidden="true">·</span>
          <span className="dataset-context-stats">
            <strong>{DATASET_STATS.total}</strong> Documents (
            <span>{DATASET_STATS.slack} Slack</span> ·{' '}
            <span>{DATASET_STATS.linear} Linear</span> ·{' '}
            <span>{DATASET_STATS.github} GitHub</span>)
          </span>
        </div>
        <div className="dataset-context-right">
          <span className="dataset-mode-pill">Idempotent Graph Slice</span>
        </div>
      </div>

      {/* Search & Category Filter Toolbar */}
      <div className="suggestions-toolbar" role="search">
        <div className="suggestions-search-row">
          <input
            className="suggestions-search-input"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by keyword, entity (e.g. PR-99501), issue key (e.g. ENG-30521)..."
            aria-label="Filter suggestions"
          />
          {search && (
            <button
              className="search-clear-btn"
              onClick={() => setSearch('')}
              aria-label="Clear search filter"
              type="button"
            >
              ✕
            </button>
          )}
        </div>

        <div className="suggestions-category-tabs" role="tablist" aria-label="Filter by category">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              className={`category-tab ${category === cat.id ? 'active' : ''}`}
              onClick={() => setCategory(cat.id)}
              role="tab"
              aria-selected={category === cat.id}
              type="button"
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Suggestions Count Line */}
      <div className="suggestions-meta-line" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>
          Showing <strong>{filtered.length}</strong> of {SUGGESTIONS_CATALOG.length} investigations
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className={`quota-status-tag ${quota.isExceeded ? 'exceeded' : ''}`} title="Demo Quota">
            <span>Quota:</span>
            <strong>{quota.remaining} / {quota.maxQuota} remaining</strong>
          </div>
          {(category !== 'ALL' || search) && (
            <button
              className="clear-all-filters-btn"
              onClick={handleClearFilters}
              type="button"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Suggestions List Table */}
      {filtered.length > 0 ? (
        <div className="suggestions-list-table-container">
          <table className="suggestions-list-table" aria-label="Investigation Suggestions List">
            <thead>
              <tr>
                <th scope="col" style={{ width: '58%' }}>INVESTIGATION QUERY & TOPIC</th>
                <th scope="col" style={{ width: '22%' }}>SOURCE & TARGET</th>
                <th scope="col" style={{ width: '20%', textAlign: 'right' }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id} className="suggestion-list-row">
                  <td className="sug-col-query">
                    <div className="sug-list-title-row">
                      <span className="sug-list-title">{item.title}</span>
                    </div>
                    <div className="sug-list-desc">{item.description}</div>
                    {item.tags && item.tags.length > 0 && (
                      <div className="sug-list-tags">
                        {item.tags.map((t) => (
                          <button
                            key={t}
                            className="card-tag-pill"
                            onClick={() => handleTagClick(t)}
                            type="button"
                            title={`Filter by "${t}"`}
                          >
                            {t}
                          </button>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="sug-col-meta">
                    <div className="sug-meta-badges">
                      <span className={`cat-badge ${item.category.toLowerCase()}`}>
                        {item.badge}
                      </span>
                      <span className={`source-badge ${item.source.toLowerCase()}`}>
                        {item.source}
                      </span>
                    </div>
                    {item.entity && (
                      <div style={{ marginTop: '6px' }}>
                        <span className="card-entity-tag" title={`Target Entity: ${item.entity}`}>
                          {item.entity}
                        </span>
                      </div>
                    )}
                  </td>
                  <td className="sug-col-actions">
                    <div className="entity-actions-inline">
                      <button
                        className="entity-action-btn ask-btn"
                        onClick={() => handleQueryClick(item.query)}
                        aria-label={`Ask Veridex: ${item.query}`}
                        type="button"
                      >
                        <span>ASK</span>
                        <span aria-hidden="true">→</span>
                      </button>
                      {item.entity && (
                        <button
                          className="entity-action-btn trace-btn"
                          onClick={() => handleTraceClick(item.entity)}
                          aria-label={`Trace dependencies for ${item.entity}`}
                          type="button"
                        >
                          <span>TRACE</span>
                          <span aria-hidden="true">⟷</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-block suggestions-empty-block" role="status">
          <div className="empty-label">No Investigations Found</div>
          <div className="empty-desc">
            No indexed suggestions matched your search &ldquo;{search}&rdquo; in category &ldquo;{category}&rdquo;.
          </div>
          <button
            className="lp-btn-primary lp-btn-sm"
            onClick={handleClearFilters}
            style={{ marginTop: '16px' }}
            type="button"
          >
            Show All Suggestions
          </button>
        </div>
      )}
    </section>
  )
}
