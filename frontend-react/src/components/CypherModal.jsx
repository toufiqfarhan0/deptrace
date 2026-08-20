import React, { useState } from 'react'

export default function CypherModal({ isOpen, onClose, cypherInfo, title = 'HydraDB OpenCypher Query Inspector' }) {
  const [copied, setCopied] = useState(false)

  if (!isOpen || !cypherInfo) return null

  const queryText = typeof cypherInfo === 'string' ? cypherInfo : cypherInfo.query || ''
  const purpose = cypherInfo.purpose || 'Deterministic graph query executed in HydraDB'
  const nodes = cypherInfo.nodes_matched || []
  const rels = cypherInfo.relationships_traversed || []
  const predicates = cypherInfo.filtering_predicates || []
  const vectorLimitation = cypherInfo.vector_rag_limitation || ''

  const handleCopy = () => {
    if (!navigator?.clipboard) return
    navigator.clipboard.writeText(queryText).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="cypher-modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="cypher-modal-title">
      <div className="cypher-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="cypher-modal-header">
          <div className="cypher-modal-title-group">
            <span className="cypher-badge">HYDRADB OPENCYPHER</span>
            <h2 id="cypher-modal-title" className="cypher-modal-title">{title}</h2>
          </div>
          <button
            type="button"
            className="cypher-close-btn"
            onClick={onClose}
            aria-label="Close query inspector"
          >
            ✕
          </button>
        </div>

        {/* Purpose banner */}
        <div className="cypher-purpose-banner">
          <span className="purpose-dot" />
          <span className="purpose-text">{purpose}</span>
        </div>

        {/* Query Code Box */}
        <div className="cypher-code-block">
          <div className="cypher-code-topbar">
            <span className="cypher-code-label">OpenCypher Query Syntax</span>
            <button
              type="button"
              className={`cypher-copy-btn ${copied ? 'copied' : ''}`}
              onClick={handleCopy}
            >
              {copied ? '✓ Copied to Clipboard' : 'Copy OpenCypher'}
            </button>
          </div>
          <pre className="cypher-code-content">
            <code>{queryText}</code>
          </pre>
        </div>

        {/* Query Traversal Breakdown */}
        <div className="cypher-meta-grid">
          {nodes.length > 0 && (
            <div className="cypher-meta-box">
              <span className="cypher-meta-title">NODES MATCHED</span>
              <div className="cypher-tags-list">
                {nodes.map((n, i) => (
                  <span key={i} className="cypher-node-tag">{n}</span>
                ))}
              </div>
            </div>
          )}

          {rels.length > 0 && (
            <div className="cypher-meta-box">
              <span className="cypher-meta-title">RELATIONSHIPS TRAVERSED</span>
              <div className="cypher-tags-list">
                {rels.map((r, i) => (
                  <span key={i} className="cypher-rel-tag">{r}</span>
                ))}
              </div>
            </div>
          )}

          {predicates.length > 0 && (
            <div className="cypher-meta-box full-width">
              <span className="cypher-meta-title">GRAPH PREDICATES & CONSTRAINTS</span>
              <div className="cypher-tags-list">
                {predicates.map((p, i) => (
                  <span key={i} className="cypher-pred-tag">{p}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Vector RAG Limitation Note */}
        {vectorLimitation && (
          <div className="cypher-limitation-box">
            <div className="limitation-header">
              <span className="limitation-pill">WHY VECTOR RAG FAILS HERE</span>
            </div>
            <p className="limitation-body">{vectorLimitation}</p>
          </div>
        )}

        {/* Footer */}
        <div className="cypher-modal-footer">
          <span className="footer-status-text">Executed against HydraDB graph engine with zero probabilistic embedding drift.</span>
          <button type="button" className="btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
