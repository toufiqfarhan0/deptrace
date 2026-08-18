import React, { useState, useMemo } from 'react'
import {
  DATASET_STATS,
  SUGGESTIONS_CATALOG,
  getFilteredSuggestions,
} from '../data/suggestions.js'

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

  return (
    <section aria-label="Investigation suggestions catalog" className="suggestions-section">
      <div className="view-header">
        <h1 className="view-title">Start with a Real Investigation</h1>
        <div className="view-subtitle">
          Explore verified questions from the HydraDB demo knowledge graph spanning Slack, Linear, and GitHub.
        </div>
      </div>

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
      <div className="suggestions-meta-line">
        <span>
          Showing <strong>{filtered.length}</strong> of {SUGGESTIONS_CATALOG.length} investigations
        </span>
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

      {/* Suggestions Cards Grid */}
      {filtered.length > 0 ? (
        <div className="suggestions-grid">
          {filtered.map((item) => (
            <article key={item.id} className="suggestion-card" aria-label={item.title}>
              <div className="card-top-row">
                <div className="card-badges">
                  <span className={`cat-badge ${item.category.toLowerCase()}`}>
                    {item.badge}
                  </span>
                  <span className={`source-badge ${item.source.toLowerCase()}`}>
                    {item.source}
                  </span>
                </div>
                {item.entity && (
                  <span className="card-entity-tag" title="Target Entity">
                    {item.entity}
                  </span>
                )}
              </div>

              <h2 className="card-query-title">
                <span>{item.title}</span>
              </h2>

              <p className="card-desc">{item.description}</p>

              {item.tags && item.tags.length > 0 && (
                <div className="card-tags-row">
                  {item.tags.map((t) => (
                    <button
                      key={t}
                      className="card-tag-pill"
                      onClick={() => handleTagClick(t)}
                      type="button"
                      title={`Filter by "${t}"`}
                    >
                      #{t}
                    </button>
                  ))}
                </div>
              )}

              <div className="card-actions-row">
                <button
                  className="card-btn card-btn-primary"
                  onClick={() => onSelectQuery(item.query)}
                  aria-label={`Ask Veridex: ${item.query}`}
                  type="button"
                >
                  <span>ASK VERIDEX</span>
                  <span aria-hidden="true">→</span>
                </button>

                {item.entity && (
                  <button
                    className="card-btn card-btn-ghost"
                    onClick={() => onSelectTrace(item.entity)}
                    aria-label={`Trace dependencies for ${item.entity}`}
                    type="button"
                  >
                    <span>TRACE</span>
                    <span aria-hidden="true">⟷</span>
                  </button>
                )}
              </div>
            </article>
          ))}
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
