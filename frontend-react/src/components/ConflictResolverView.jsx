import React, { useState, useEffect, useMemo } from 'react'
import CypherModal from './CypherModal.jsx'
import { SourceIcon, SlackIcon, LinearIcon, GitHubIcon } from './SourceIcons.jsx'

export default function ConflictResolverView({ onNavigateToAsk, onNavigateToTrace }) {
  const [conflicts, setConflicts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedEntity, setSelectedEntity] = useState('ALL')
  const [search, setSearch] = useState('')
  const [selectedCypher, setSelectedCypher] = useState(null)

  useEffect(() => {
    let isMounted = true
    setLoading(true)
    fetch('/api/conflicts')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        if (isMounted) {
          setConflicts(data.conflicts || [])
          setLoading(false)
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message)
          setLoading(false)
        }
      })

    return () => { isMounted = false }
  }, [])

  const entities = ['ALL', 'INC-2026', 'Bluecrest', 'REL-311', 'ENG-68910']

  const filteredConflicts = useMemo(() => {
    return conflicts.filter((c) => {
      const matchesEntity =
        selectedEntity === 'ALL' ||
        c.entity.toUpperCase() === selectedEntity.toUpperCase()
      const matchesSearch =
        !search ||
        c.entity.toLowerCase().includes(search.toLowerCase()) ||
        c.topic.toLowerCase().includes(search.toLowerCase()) ||
        c.canonical_truth.fact_text.toLowerCase().includes(search.toLowerCase())
      return matchesEntity && matchesSearch
    })
  }, [conflicts, selectedEntity, search])

  return (
    <div className="conflicts-page">
      {/* Header Banner */}
      <div className="conflicts-header-block">
        <div className="conflicts-title-row">
          <div>
            <div className="conflicts-eyebrow">TRACK 01: ONTOLOGY ALIGNMENT & CONFLICT RESOLUTION</div>
            <h1 className="conflicts-heading">Provenance Truth Arbiter</h1>
            <p className="conflicts-subheading">
              Enterprise communications contain contradictory hypotheses, stale configurations, and unverified chat panic.
              Veridex deterministically determines canonical ground truth in HydraDB by analyzing graph causal paths, bi-temporal timestamps, and source authority hierarchies.
            </p>
          </div>
          <div className="conflicts-hierarchy-badge">
            <span className="hierarchy-label">AUTHORITY HIERARCHY</span>
            <div className="hierarchy-row">
              <span className="h-pill git"><GitHubIcon size={12} /> Merged Code (0.95+)</span>
              <span className="h-arrow">›</span>
              <span className="h-pill linear"><LinearIcon size={12} /> Resolved Issue (0.85)</span>
              <span className="h-arrow">›</span>
              <span className="h-pill slack"><SlackIcon size={12} /> Ephemeral Chat (0.60)</span>
            </div>
          </div>
        </div>

        {/* Filter Toolbar */}
        <div className="conflicts-toolbar">
          <div className="conflicts-chips-list">
            <span className="chips-label">Filter Entity:</span>
            {entities.map((ent) => (
              <button
                key={ent}
                type="button"
                className={`conf-filter-btn ${selectedEntity === ent ? 'active' : ''}`}
                onClick={() => setSelectedEntity(ent)}
              >
                {ent}
              </button>
            ))}
          </div>

          <div className="conflicts-search-box">
            <input
              type="text"
              placeholder="Search contradictions by topic, entity, or claim..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="conf-search-input"
            />
            {search && (
              <button type="button" className="conf-clear-btn" onClick={() => setSearch('')}>✕</button>
            )}
          </div>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="conflicts-metrics-banner">
        <div className="c-metric-item">
          <span className="c-metric-val">{conflicts.length}</span>
          <span className="c-metric-lbl">Total Cross-Source Contradictions</span>
        </div>
        <div className="c-metric-divider" />
        <div className="c-metric-item">
          <span className="c-metric-val success">100%</span>
          <span className="c-metric-lbl">Deterministic Resolution Rate</span>
        </div>
        <div className="c-metric-divider" />
        <div className="c-metric-item">
          <span className="c-metric-val">0%</span>
          <span className="c-metric-lbl">Vector RAG Blending / Hallucination</span>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="empty-block">
          <div className="empty-label">Resolving Enterprise Contradictions...</div>
          <div className="empty-desc">Evaluating bi-temporal causality and source authority in HydraDB...</div>
        </div>
      )}

      {error && (
        <div className="error-block">
          <strong>Failed to load conflict resolutions:</strong> {error}
        </div>
      )}

      {/* Conflict Resolution Cards */}
      {!loading && !error && filteredConflicts.length === 0 && (
        <div className="empty-block">
          <div className="empty-label">No Contradictions Found</div>
          <div className="empty-desc">No records matched your search or entity filter.</div>
        </div>
      )}

      <div className="conflicts-grid">
        {filteredConflicts.map((item) => (
          <div key={item.id} className="conflict-card">
            {/* Top Bar */}
            <div className="conflict-topbar">
              <div className="conflict-topic-group">
                <span className="conflict-entity-pill">{item.entity}</span>
                <h3 className="conflict-topic-title">{item.topic}</h3>
              </div>
              <span className={`conflict-status-badge status-${item.status}`}>
                {item.status.toUpperCase()}
              </span>
            </div>

            {/* Side-by-Side Comparison Container */}
            <div className="conflict-comparison-grid">
              {/* Canonical Ground Truth (Winner) */}
              <div className="truth-col canonical-col">
                <div className="truth-col-header canonical-header">
                  <div className="truth-title-left">
                    <span className="truth-status-dot canonical-dot" />
                    <span className="truth-heading">CANONICAL GROUND TRUTH</span>
                  </div>
                  <span className="authority-score-pill">
                    Authority: {Math.round(item.canonical_truth.authority_score * 100)}%
                  </span>
                </div>

                <div className="truth-card-body">
                  <p className="truth-fact-text">{item.canonical_truth.fact_text}</p>
                  
                  <div className="truth-meta-row">
                    <span className={`source-pill source-${item.canonical_truth.source}`}>
                      <SourceIcon source={item.canonical_truth.source} size={13} style={{ marginRight: 4 }} />
                      {item.canonical_truth.source_ref}
                    </span>
                    {item.canonical_truth.timestamp && (
                      <span className="truth-timestamp">{item.canonical_truth.timestamp}</span>
                    )}
                  </div>

                  <div className="truth-verification-line">
                    <strong>Verification:</strong> {item.canonical_truth.verification_method}
                  </div>
                </div>
              </div>

              {/* Contradicting / Superseded Claims */}
              <div className="truth-col superseded-col">
                <div className="truth-col-header superseded-header">
                  <div className="truth-title-left">
                    <span className="truth-status-dot superseded-dot" />
                    <span className="truth-heading">CONTRADICTING / SUPERSEDED CLAIMS</span>
                  </div>
                  <span className="superseded-count-pill">
                    {item.contradicting_claims.length} Claim{item.contradicting_claims.length === 1 ? '' : 's'} Refuted
                  </span>
                </div>

                <div className="superseded-claims-list">
                  {item.contradicting_claims.map((claim, cIdx) => (
                    <div key={cIdx} className="superseded-claim-card">
                      <p className="superseded-claim-text">&ldquo;{claim.claim_text}&rdquo;</p>
                      
                      <div className="claim-meta-row">
                        <span className={`source-pill source-${claim.source}`}>
                          <SourceIcon source={claim.source} size={12} style={{ marginRight: 4 }} />
                          {claim.source_ref}
                        </span>
                        <span className="claim-status-tag">{claim.status.toUpperCase()}</span>
                      </div>

                      <div className="superseded-reason-box">
                        <span className="reason-label">Refutation Reason:</span> {claim.superseded_reason}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Resolution Reasoning Box */}
            <div className="resolution-reasoning-box">
              <div className="reasoning-header">
                <span className="reasoning-badge">HYDRADB RESOLUTION LOGIC</span>
              </div>
              <p className="reasoning-content">{item.resolution_reasoning}</p>
            </div>

            {/* Bottom Actions Bar */}
            <div className="conflict-card-footer">
              <div className="footer-actions-left">
                {item.cypher_inspection && (
                  <button
                    type="button"
                    className="cypher-inspect-trigger-btn"
                    onClick={() => setSelectedCypher(item.cypher_inspection)}
                  >
                    Inspect HydraDB Cypher Query →
                  </button>
                )}
              </div>

              <div className="footer-actions-right">
                {onNavigateToAsk && (
                  <button
                    type="button"
                    className="btn-outline-sm"
                    onClick={() => onNavigateToAsk(`What is the verified resolution for ${item.entity}?`)}
                  >
                    Ask RAG →
                  </button>
                )}
                {onNavigateToTrace && (
                  <button
                    type="button"
                    className="btn-outline-sm"
                    onClick={() => onNavigateToTrace(item.entity)}
                  >
                    Trace Graph →
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Cypher Query Modal */}
      <CypherModal
        isOpen={Boolean(selectedCypher)}
        onClose={() => setSelectedCypher(null)}
        cypherInfo={selectedCypher}
        title="HydraDB Conflict Resolution Cypher Query"
      />
    </div>
  )
}
