import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { SourceIcon, SlackIcon, LinearIcon, GitHubIcon, JiraIcon, ConfluenceIcon, PagerDutyIcon } from './SourceIcons.jsx'

export default function GraphExplorerView({ onNavigateToAsk, onNavigateToTrace, onNavigateToTimeline }) {
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Canvas Transform State: Pan & Zoom
  const [zoom, setZoom] = useState(1.0)
  const [pan, setPan] = useState({ x: 40, y: 30 })
  const [isPanning, setIsPanning] = useState(false)
  const panStartRef = useRef({ x: 0, y: 0 })

  // Node Positions (supports live dragging)
  const [nodePositions, setNodePositions] = useState({})
  const [draggedNodeId, setDraggedNodeId] = useState(null)
  const dragOffsetRef = useRef({ x: 0, y: 0 })

  // Selection & Hover
  const [selectedNode, setSelectedNode] = useState(null)
  const [hoveredEdge, setHoveredEdge] = useState(null)
  const [hoveredNode, setHoveredNode] = useState(null)

  // Filters
  const [sourceFilter, setSourceFilter] = useState('ALL')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  const svgRef = useRef(null)

  useEffect(() => {
    let isMounted = true
    setLoading(true)
    fetch('/api/graph/full')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        if (isMounted) {
          setGraphData(data)
          // Initialize node coordinate map
          const posMap = {}
          data.nodes.forEach((n) => {
            posMap[n.id] = { x: n.initial_x || 400, y: n.initial_y || 250 }
          })
          setNodePositions(posMap)
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

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(2.5, z + 0.15))
  const handleZoomOut = () => setZoom((z) => Math.max(0.4, z - 0.15))
  const handleResetView = () => {
    setZoom(1.0)
    setPan({ x: 40, y: 30 })
  }

  // Wheel zoom
  const handleWheel = (e) => {
    e.preventDefault()
    const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92
    setZoom((z) => Math.min(2.5, Math.max(0.4, z * zoomFactor)))
  }

  // Canvas Pan Handlers
  const handleMouseDownCanvas = (e) => {
    if (e.target.tagName === 'svg' || e.target.classList.contains('canvas-background')) {
      setIsPanning(true)
      panStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y }
    }
  }

  const handleMouseMove = (e) => {
    if (isPanning) {
      setPan({
        x: e.clientX - panStartRef.current.x,
        y: e.clientY - panStartRef.current.y,
      })
    } else if (draggedNodeId) {
      const svg = svgRef.current
      if (!svg) return
      const rect = svg.getBoundingClientRect()
      const mouseX = (e.clientX - rect.left - pan.x) / zoom
      const mouseY = (e.clientY - rect.top - pan.y) / zoom

      setNodePositions((prev) => ({
        ...prev,
        [draggedNodeId]: {
          x: mouseX - dragOffsetRef.current.x,
          y: mouseY - dragOffsetRef.current.y,
        },
      }))
    }
  }

  const handleMouseUp = () => {
    setIsPanning(false)
    setDraggedNodeId(null)
  }

  // Node Drag Handlers
  const handleNodeMouseDown = (e, nodeId) => {
    e.stopPropagation()
    setDraggedNodeId(nodeId)
    const nodePos = nodePositions[nodeId] || { x: 0, y: 0 }
    const svg = svgRef.current
    if (!svg) return
    const rect = svg.getBoundingClientRect()
    const mouseX = (e.clientX - rect.left - pan.x) / zoom
    const mouseY = (e.clientY - rect.top - pan.y) / zoom
    dragOffsetRef.current = { x: mouseX - nodePos.x, y: mouseY - nodePos.y }
  }

  // Node Color Helper
  const getNodeColor = (type, source) => {
    if (type === 'incident') return '#EF4444' // Red
    if (type === 'pull_request') return '#10B981' // Green
    if (type === 'linear_issue') return '#6366F1' // Indigo
    if (type === 'jira_ticket') return '#2684FF' // Jira Blue
    if (type === 'confluence_rfc') return '#0052CC' // Confluence Dark Blue
    if (source === 'pagerduty') return '#F59E0B' // Amber
    return '#06B6D4' // Cyan / Teal
  }

  // Filtered Nodes & Edges
  const { visibleNodes, visibleEdges } = useMemo(() => {
    if (!graphData) return { visibleNodes: [], visibleEdges: [] }

    const filteredNodes = graphData.nodes.filter((n) => {
      const matchSource = sourceFilter === 'ALL' || n.source.toUpperCase() === sourceFilter.toUpperCase()
      const matchType = typeFilter === 'ALL' || n.type.toUpperCase() === typeFilter.toUpperCase()
      const matchSearch =
        !searchQuery ||
        n.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.title.toLowerCase().includes(searchQuery.toLowerCase())
      return matchSource && matchType && matchSearch
    })

    const visibleNodeIds = new Set(filteredNodes.map((n) => n.id))

    const filteredEdges = graphData.edges.filter((e) => {
      return visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
    })

    return { visibleNodes: filteredNodes, visibleEdges: filteredEdges }
  }, [graphData, sourceFilter, typeFilter, searchQuery])

  const sourcesList = ['ALL', 'GITHUB', 'LINEAR', 'SLACK', 'JIRA', 'CONFLUENCE', 'PAGERDUTY']
  const typesList = ['ALL', 'INCIDENT', 'PULL_REQUEST', 'LINEAR_ISSUE', 'JIRA_TICKET', 'CONFLUENCE_RFC', 'SERVICE', 'COMPONENT']

  return (
    <div className="graph-explorer-page">
      {/* Top Header */}
      <div className="graph-explorer-header">
        <div className="graph-title-row">
          <div>
            <div className="conflicts-eyebrow">INTERACTIVE GRAPH ENGINE · HYDRADB CLOUD V2</div>
            <h1 className="conflicts-heading">Knowledge Graph Canvas Explorer</h1>
            <p className="conflicts-subheading">
              Explore the live multi-source enterprise dependency topology. Drag nodes, zoom/pan the canvas, inspect typed relationships across <strong>Slack, Linear, GitHub, Jira, and Confluence</strong>.
            </p>
          </div>
          {graphData && (
            <div className="graph-stats-pills">
              <span className="stat-badge"><strong>{graphData.total_nodes}</strong> Entities</span>
              <span className="stat-badge"><strong>{graphData.total_edges}</strong> Relations</span>
              <span className="stat-badge success"><strong>6</strong> Enterprise Sources</span>
            </div>
          )}
        </div>

        {/* Filter Controls Bar */}
        <div className="graph-toolbar">
          <div className="toolbar-group">
            <span className="chips-label">Source:</span>
            <div className="chips-row">
              {sourcesList.map((src) => (
                <button
                  key={src}
                  type="button"
                  className={`conf-filter-btn ${sourceFilter === src ? 'active' : ''}`}
                  onClick={() => setSourceFilter(src)}
                >
                  {src}
                </button>
              ))}
            </div>
          </div>

          <div className="toolbar-group">
            <span className="chips-label">Type:</span>
            <div className="chips-row">
              {typesList.map((tp) => (
                <button
                  key={tp}
                  type="button"
                  className={`conf-filter-btn ${typeFilter === tp ? 'active' : ''}`}
                  onClick={() => setTypeFilter(tp)}
                >
                  {tp.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          <div className="graph-search-box">
            <input
              type="text"
              placeholder="Search node (e.g. JIRA-4029, PR-99501)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="conf-search-input"
            />
            {searchQuery && (
              <button type="button" className="conf-clear-btn" onClick={() => setSearchQuery('')}>✕</button>
            )}
          </div>
        </div>
      </div>

      {/* Main Canvas Container */}
      <div className="graph-canvas-workspace">
        {loading && (
          <div className="empty-block" style={{ height: 480 }}>
            <div className="empty-label">Loading Graph Topology...</div>
            <div className="empty-desc">Extracting enterprise graph nodes and typed edges from HydraDB...</div>
          </div>
        )}

        {error && (
          <div className="error-block">
            <strong>Failed to load graph:</strong> {error}
          </div>
        )}

        {!loading && !error && (
          <div className="canvas-wrapper" onMouseDown={handleMouseDownCanvas} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}>
            {/* Canvas Floating Controls */}
            <div className="canvas-floating-controls">
              <button type="button" className="canvas-ctrl-btn" onClick={handleZoomIn} title="Zoom In">+</button>
              <button type="button" className="canvas-ctrl-btn" onClick={handleZoomOut} title="Zoom Out">−</button>
              <button type="button" className="canvas-ctrl-btn" onClick={handleResetView} title="Reset View">⟲</button>
              <span className="zoom-level-text">{Math.round(zoom * 100)}%</span>
            </div>

            {/* SVG Force Canvas */}
            <svg
              ref={svgRef}
              className="graph-canvas-svg"
              onWheel={handleWheel}
            >
              <defs>
                <marker
                  id="canvas-arrow"
                  viewBox="0 0 10 10"
                  refX="22"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--c-border-strong)" />
                </marker>
                <filter id="canvas-glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              <rect width="100%" height="100%" fill="transparent" className="canvas-background" />

              <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                {/* 1. Render Edges */}
                {visibleEdges.map((edge) => {
                  const sPos = nodePositions[edge.source] || { x: 300, y: 200 }
                  const tPos = nodePositions[edge.target] || { x: 500, y: 200 }
                  const isEdgeHovered = hoveredEdge?.id === edge.id
                  const isConnectedToHovered =
                    hoveredNode && (edge.source === hoveredNode.id || edge.target === hoveredNode.id)

                  const midX = (sPos.x + tPos.x) / 2
                  const midY = (sPos.y + tPos.y) / 2

                  return (
                    <g
                      key={edge.id}
                      className={`canvas-edge-group ${isEdgeHovered || isConnectedToHovered ? 'active' : ''}`}
                      onMouseEnter={() => setHoveredEdge(edge)}
                      onMouseLeave={() => setHoveredEdge(null)}
                    >
                      <line
                        x1={sPos.x}
                        y1={sPos.y}
                        x2={tPos.x}
                        y2={tPos.y}
                        stroke={isEdgeHovered || isConnectedToHovered ? 'var(--c-accent)' : 'var(--c-border-strong)'}
                        strokeWidth={isEdgeHovered || isConnectedToHovered ? 2.5 : 1.4}
                        strokeDasharray={edge.type === 'SUPERSEDES' ? '4 3' : undefined}
                        markerEnd="url(#canvas-arrow)"
                      />
                      {/* Edge Label Pill */}
                      <g transform={`translate(${midX}, ${midY})`}>
                        <rect
                          x="-32"
                          y="-9"
                          width="64"
                          height="18"
                          rx="4"
                          fill="var(--c-surface)"
                          stroke={isEdgeHovered ? 'var(--c-accent)' : 'var(--c-border)'}
                          strokeWidth="1"
                        />
                        <text
                          textAnchor="middle"
                          dy="3.5"
                          fontSize="7.5"
                          fontWeight="700"
                          fontFamily="var(--font-mono)"
                          fill={isEdgeHovered ? 'var(--c-accent)' : 'var(--c-text-3)'}
                        >
                          {edge.label}
                        </text>
                      </g>
                    </g>
                  )
                })}

                {/* 2. Render Nodes */}
                {visibleNodes.map((node) => {
                  const pos = nodePositions[node.id] || { x: 400, y: 250 }
                  const isSelected = selectedNode?.id === node.id
                  const isHovered = hoveredNode?.id === node.id
                  const color = getNodeColor(node.type, node.source)

                  return (
                    <g
                      key={node.id}
                      className={`canvas-node-group ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
                      onClick={() => setSelectedNode(node)}
                      onMouseEnter={() => setHoveredNode(node)}
                      onMouseLeave={() => setHoveredNode(null)}
                      style={{ cursor: 'grab' }}
                    >
                      {/* Selection Aura */}
                      {(isSelected || isHovered) && (
                        <circle r="26" fill="none" stroke={color} strokeWidth="2" opacity="0.4" />
                      )}

                      {/* Main Node Circle */}
                      <circle
                        r="18"
                        fill="var(--c-surface)"
                        stroke={color}
                        strokeWidth={isSelected ? 3 : 2}
                        filter={isSelected || isHovered ? 'url(#canvas-glow)' : undefined}
                      />

                      {/* Center Node Type Abbreviation */}
                      <text
                        textAnchor="middle"
                        dy="3.5"
                        fontSize="7.5"
                        fontWeight="800"
                        fill="var(--c-text)"
                        pointerEvents="none"
                      >
                        {node.type === 'incident' ? 'INC' : (node.type === 'pull_request' ? 'PR' : (node.type === 'jira_ticket' ? 'JIRA' : (node.type === 'confluence_rfc' ? 'RFC' : 'NODE')))}
                      </text>

                      {/* Node Label Below */}
                      <text
                        textAnchor="middle"
                        dy="30"
                        fontSize="9.5"
                        fontWeight="700"
                        fontFamily="var(--font-mono)"
                        fill="var(--c-text)"
                        pointerEvents="none"
                      >
                        {node.label}
                      </text>
                    </g>
                  )
                })}
              </g>
            </svg>

            {/* Edge Hover Tooltip */}
            {hoveredEdge && (
              <div className="canvas-edge-tooltip">
                <div className="tooltip-header">
                  <span className="tooltip-type">{hoveredEdge.type}</span>
                  <span className="tooltip-source">{hoveredEdge.source_system.toUpperCase()}</span>
                </div>
                <div className="tooltip-body">{hoveredEdge.statement}</div>
              </div>
            )}

            {/* Selected Node Details Drawer */}
            {selectedNode && (
              <div className="canvas-node-drawer">
                <div className="drawer-header">
                  <div className="drawer-title-group">
                    <span className="drawer-type-pill" style={{ color: getNodeColor(selectedNode.type, selectedNode.source) }}>
                      <SourceIcon source={selectedNode.source} size={12} style={{ marginRight: 4 }} />
                      {selectedNode.type.toUpperCase()}
                    </span>
                    <h3 className="drawer-node-name">{selectedNode.label}</h3>
                  </div>
                  <button type="button" className="drawer-close-btn" onClick={() => setSelectedNode(null)}>✕</button>
                </div>

                <div className="drawer-body">
                  <p className="drawer-title-text">{selectedNode.title}</p>
                  <p className="drawer-summary-text">{selectedNode.summary}</p>

                  <div className="drawer-meta-grid">
                    <div className="d-meta-item">
                      <span className="d-meta-lbl">Authority</span>
                      <span className="d-meta-val">{Math.round(selectedNode.authority_score * 100)}%</span>
                    </div>
                    <div className="d-meta-item">
                      <span className="d-meta-lbl">Status</span>
                      <span className="d-meta-val">{selectedNode.status.toUpperCase()}</span>
                    </div>
                    <div className="d-meta-item">
                      <span className="d-meta-lbl">Source</span>
                      <span className="d-meta-val">{selectedNode.source.toUpperCase()}</span>
                    </div>
                  </div>

                  {/* Statements */}
                  <div className="drawer-statements-section">
                    <span className="d-sec-title">VERIFIED STATEMENTS IN HYDRADB</span>
                    <div className="d-statements-list">
                      {selectedNode.statements.map((s, idx) => (
                        <div key={idx} className="d-statement-chip">{s}</div>
                      ))}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="drawer-actions-row">
                    {onNavigateToAsk && (
                      <button
                        type="button"
                        className="lp-btn-primary lp-btn-sm"
                        onClick={() => onNavigateToAsk(`What is ${selectedNode.label} about?`)}
                      >
                        Ask RAG →
                      </button>
                    )}
                    {onNavigateToTrace && (
                      <button
                        type="button"
                        className="btn-outline-sm"
                        onClick={() => onNavigateToTrace(selectedNode.label)}
                      >
                        Trace Graph →
                      </button>
                    )}
                    {onNavigateToTimeline && selectedNode.type === 'incident' && (
                      <button
                        type="button"
                        className="btn-outline-sm"
                        onClick={() => onNavigateToTimeline(selectedNode.label)}
                      >
                        Timeline →
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
