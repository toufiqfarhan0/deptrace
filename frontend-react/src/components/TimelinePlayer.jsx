import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { SourceIcon, SlackIcon, LinearIcon, GitHubIcon } from './SourceIcons'
import CypherModal from './CypherModal.jsx'

export default function TimelinePlayer({
  initialEntity = 'INC-2026',
  onNavigateToAsk,
  onNavigateToTrace,
  isActive = true,
}) {
  const [entity, setEntity] = useState(initialEntity || 'INC-2026')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [timelineData, setTimelineData] = useState(null)
  const [featuredIncidents, setFeaturedIncidents] = useState([])

  // Playback state
  const [currentStep, setCurrentStep] = useState(1)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1) // 0.5, 1, 2, 3
  const [selectedNode, setSelectedNode] = useState(null)
  const [showCypher, setShowCypher] = useState(false)

  const playTimerRef = useRef(null)
  const eventCardsRef = useRef({})
  const prevInitialEntityRef = useRef(initialEntity)

  // Load featured incidents once on mount
  useEffect(() => {
    async function fetchFeatured() {
      try {
        const res = await fetch('/api/timeline/incidents')
        if (res.ok) {
          const data = await res.json()
          setFeaturedIncidents(data)
        }
      } catch {
        // Fallback static list
      }
    }
    fetchFeatured()
  }, [])

  // Fetch timeline data for target entity
  const loadTimeline = useCallback(async (target) => {
    const queryTarget = (target !== undefined ? target : entity || 'INC-2026').trim()
    if (!queryTarget) return

    setLoading(true)
    setError(null)
    setIsPlaying(false)
    if (playTimerRef.current) clearInterval(playTimerRef.current)

    try {
      const res = await fetch(`/api/timeline?entity=${encodeURIComponent(queryTarget)}`)
      if (!res.ok) {
        throw new Error(`Failed to load timeline: HTTP ${res.status}`)
      }
      const data = await res.json()
      if (!data.found || data.total_events === 0) {
        setError(data.error || `No incident events found for '${queryTarget}'`)
        setTimelineData(null)
      } else {
        setTimelineData(data)
        setEntity(queryTarget)
        setCurrentStep(1)
      }
    } catch (err) {
      setError(err.message || 'Error connecting to timeline server')
      setTimelineData(null)
    } finally {
      setLoading(false)
    }
  }, [entity])

  // Initial load on mount
  useEffect(() => {
    loadTimeline(initialEntity || 'INC-2026')
  }, [])

  // Reload only when initialEntity prop changes from external navigation
  useEffect(() => {
    if (initialEntity && initialEntity !== prevInitialEntityRef.current) {
      prevInitialEntityRef.current = initialEntity
      setEntity(initialEntity)
      loadTimeline(initialEntity)
    }
  }, [initialEntity, loadTimeline])

  // Playback timer handling
  useEffect(() => {
    if (isPlaying && timelineData && timelineData.events.length > 1) {
      const intervalMs = Math.max(800, 2400 / playbackSpeed)
      playTimerRef.current = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= timelineData.events.length) {
            setIsPlaying(false)
            return prev
          }
          return prev + 1
        })
      }, intervalMs)
    } else if (playTimerRef.current) {
      clearInterval(playTimerRef.current)
    }

    return () => {
      if (playTimerRef.current) clearInterval(playTimerRef.current)
    }
  }, [isPlaying, playbackSpeed, timelineData])

  // Auto-scroll active event card into view
  useEffect(() => {
    const cardEl = eventCardsRef.current[currentStep]
    if (cardEl) {
      cardEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [currentStep])

  // Controls
  const handleTogglePlay = () => {
    if (timelineData && currentStep >= timelineData.events.length) {
      // Loop back to start if finished
      setCurrentStep(1)
      setIsPlaying(true)
    } else {
      setIsPlaying((prev) => !prev)
    }
  }

  const handleStepForward = () => {
    setIsPlaying(false)
    if (timelineData) {
      setCurrentStep((prev) => Math.min(prev + 1, timelineData.events.length))
    }
  }

  const handleStepBackward = () => {
    setIsPlaying(false)
    setCurrentStep((prev) => Math.max(prev - 1, 1))
  }

  const handleReset = () => {
    setIsPlaying(false)
    setCurrentStep(1)
  }

  const handleSliderChange = (e) => {
    setIsPlaying(false)
    setCurrentStep(parseInt(e.target.value, 10))
  }

  const handleSelectIncident = (incId) => {
    setEntity(incId)
    loadTimeline(incId)
  }

  const events = timelineData?.events || []
  const totalSteps = events.length || 1
  const activeEvent = events[currentStep - 1] || null

  // Active nodes & edges visible up to current step
  const visibleNodes = (timelineData?.all_nodes || []).filter(
    (n) => n.introduced_at_step <= currentStep
  )
  const visibleEdges = (timelineData?.all_edges || []).filter(
    (e) => e.introduced_at_step <= currentStep
  )

  // Stable, static coordinate map for all nodes across the entire incident
  const nodePositionMap = React.useMemo(() => {
    const all = timelineData?.all_nodes || []
    const total = all.length
    const cx = 280
    const cy = 200
    const map = new Map()

    all.forEach((node, idx) => {
      if (idx === 0) {
        map.set(node.id, { x: cx, y: cy })
        return
      }
      const nrIdx = idx - 1
      const nrTot = Math.max(total - 1, 1)

      if (nrTot <= 7) {
        const angle = (nrIdx / nrTot) * 2 * Math.PI - Math.PI / 2
        map.set(node.id, {
          x: cx + 115 * Math.cos(angle),
          y: cy + 115 * Math.sin(angle),
        })
      } else {
        const isOuter = nrIdx % 2 === 1
        const r = isOuter ? 150 : 92
        const angle = (nrIdx / nrTot) * 2 * Math.PI - Math.PI / 2
        map.set(node.id, {
          x: cx + r * Math.cos(angle),
          y: cy + r * Math.sin(angle),
        })
      }
    })

    return map
  }, [timelineData])

  const getSourceColor = (source) => {
    switch (source?.toLowerCase()) {
      case 'slack': return 'var(--c-source-slack, #ec4899)'
      case 'linear': return 'var(--c-source-linear, #6366f1)'
      case 'github': return 'var(--c-source-github, #10b981)'
      case 'person': return 'var(--c-source-person, #f59e0b)'
      default: return 'var(--c-accent, #3b82f6)'
    }
  }

  const getPhaseBadgeClass = (phase) => {
    switch (phase) {
      case 'detection': return 'phase-badge-detection'
      case 'investigation': return 'phase-badge-investigation'
      case 'mitigation': return 'phase-badge-mitigation'
      case 'resolution': return 'phase-badge-resolution'
      default: return 'phase-badge-default'
    }
  }

  return (
    <div className="timeline-page">
      {/* 1. Header & Selector */}
      <div className="timeline-header-block">
        <div className="timeline-title-row">
          <div className="timeline-title-meta">
            <h1 className="timeline-heading">
              INCIDENT TIMELINE PLAYER
            </h1>
            <p className="timeline-subheading">
              Bi-temporal multi-source replay: scrub through incidents chronologically across Slack, Linear, and GitHub.
            </p>
          </div>

          <form
            className="timeline-search-form"
            onSubmit={(e) => {
              e.preventDefault()
              loadTimeline(entity)
            }}
          >
            <input
              type="text"
              className="timeline-search-input"
              value={entity}
              onChange={(e) => setEntity(e.target.value)}
              placeholder="Enter incident or entity key (e.g. INC-2026, REL-311)..."
              aria-label="Target incident entity"
            />
            <button
              type="submit"
              className="timeline-load-btn"
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Load Replay'}
            </button>
          </form>
        </div>

        {/* Featured Incident Presets */}
        <div className="timeline-presets-bar">
          <span className="timeline-presets-label">FEATURED SCENARIOS:</span>
          <div className="timeline-presets-list">
            {(featuredIncidents.length > 0 ? featuredIncidents : [
              { id: 'INC-2026', title: 'INC-2026 (OOM Outage)' },
              { id: 'REL-311', title: 'REL-311 (Tokenizer Fallback)' },
              { id: 'PR-99501', title: 'PR-99501 (Hotfix Revert)' },
              { id: 'Bluecrest', title: 'Bluecrest (KMS Rate Limit)' },
              { id: 'kernel-selector', title: 'kernel-selector (Queue Block)' },
            ]).map((inc) => (
              <button
                key={inc.id}
                type="button"
                className={`timeline-preset-btn ${(entity || '').trim().toUpperCase() === (inc.id || '').trim().toUpperCase() ? 'active' : ''}`}
                onClick={() => handleSelectIncident(inc.id)}
              >
                <strong>{inc.id}</strong>
                {inc.severity && <span className="preset-sev-tag">{inc.severity}</span>}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="timeline-error-banner" role="alert">
          <span className="error-icon" aria-hidden="true">!</span>
          <span>{error}</span>
        </div>
      )}

      {/* 2. Interactive VCR Player Controls Bar */}
      {timelineData && (
        <div className="timeline-player-rail">
          <div className="timeline-rail-top">
            <div className="timeline-transport-controls">
              <button
                type="button"
                className="transport-btn reset-btn"
                onClick={handleReset}
                title="Reset to start"
                aria-label="Reset playback"
              >
                &#x23EE;
              </button>
              <button
                type="button"
                className="transport-btn step-btn"
                onClick={handleStepBackward}
                disabled={currentStep <= 1}
                title="Step backward"
                aria-label="Step backward"
              >
                &#x25C0;
              </button>
              <button
                type="button"
                className={`transport-btn play-btn ${isPlaying ? 'playing' : ''}`}
                onClick={handleTogglePlay}
                title={isPlaying ? 'Pause replay' : (currentStep >= totalSteps ? 'Replay from start' : 'Play timeline replay')}
                aria-label={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? 'PAUSE' : (currentStep >= totalSteps ? 'REPLAY' : 'PLAY')}
              </button>
              <button
                type="button"
                className="transport-btn step-btn"
                onClick={handleStepForward}
                disabled={currentStep >= totalSteps}
                title="Step forward"
                aria-label="Step forward"
              >
                &#x25B6;
              </button>
            </div>

            {/* Scrubber Info */}
            <div className="timeline-step-indicator">
              <span className="step-counter">
                STEP <strong>{currentStep}</strong> / {totalSteps}
              </span>
              <span className="step-delta-badge">
                {activeEvent?.relative_time || '+0m'}
              </span>
              {activeEvent && (
                <span className={`phase-badge ${getPhaseBadgeClass(activeEvent.phase)}`}>
                  {activeEvent.phase_label}
                </span>
              )}
            </div>

            {/* Speed Selector */}
            <div className="timeline-speed-selector" role="group" aria-label="Playback speed">
              <span className="speed-lbl">SPEED:</span>
              {[0.5, 1, 2, 3].map((spd) => (
                <button
                  key={spd}
                  type="button"
                  className={`speed-pill ${playbackSpeed === spd ? 'active' : ''}`}
                  onClick={() => setPlaybackSpeed(spd)}
                >
                  {spd}x
                </button>
              ))}
            </div>

            {/* Cypher Inspector Trigger */}
            {timelineData?.cypher_inspection && (
              <button
                type="button"
                className="cypher-mini-btn"
                onClick={() => setShowCypher(true)}
                title="Inspect HydraDB OpenCypher Timeline Query"
              >
                Inspect Cypher Query
              </button>
            )}
          </div>

          {/* Interactive Scrub Track */}
          <div className="timeline-scrub-track-wrapper">
            <input
              type="range"
              min="1"
              max={totalSteps}
              value={currentStep}
              onChange={handleSliderChange}
              className="timeline-slider"
              aria-label="Incident timeline scrubber"
              style={{
                background: `linear-gradient(to right, var(--c-accent) 0%, var(--c-accent) ${totalSteps > 1 ? ((currentStep - 1) / (totalSteps - 1)) * 100 : 0}%, var(--c-surface-3) ${totalSteps > 1 ? ((currentStep - 1) / (totalSteps - 1)) * 100 : 0}%, var(--c-surface-3) 100%)`
              }}
            />
            <div className="timeline-track-ticks">
              {events.map((evt, idx) => (
                <div
                  key={evt.id}
                  className={`timeline-tick ${idx + 1 <= currentStep ? 'active' : ''} ${idx + 1 === currentStep ? 'current' : ''} ${idx === 0 ? 'tick-first' : ''} ${idx === totalSteps - 1 ? 'tick-last' : ''}`}
                  style={{ left: `${(idx / Math.max(totalSteps - 1, 1)) * 100}%` }}
                  onClick={() => {
                    setIsPlaying(false)
                    setCurrentStep(idx + 1)
                  }}
                  title={`Step ${idx + 1}: ${evt.title}`}
                >
                  <span className="tick-marker" />
                  <span className="tick-time">{evt.relative_time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 3. Main Split View: Graph State (Left) + Event Feed (Right) */}
      {timelineData && (
        <div className="timeline-split-grid">
          {/* Left Column: Dynamic Graph Evolution */}
          <div className="timeline-graph-panel">
            <div className="panel-header">
              <div className="panel-title">
                <span>DYNAMIC GRAPH TOPOLOGY</span>
                <span className="panel-badge">
                  {visibleNodes.length} Nodes · {visibleEdges.length} Relations (Step {currentStep})
                </span>
              </div>
              <div className="graph-time-stamp">
                Virtual Time: <code>{activeEvent?.timestamp ? new Date(activeEvent.timestamp).toLocaleTimeString() : 'T+0m'}</code>
              </div>
            </div>

            {/* Interactive Graph Canvas */}
            <div className="temporal-graph-canvas">
              <svg className="temporal-graph-svg" viewBox="0 0 560 400" preserveAspectRatio="xMidYMid meet">
                <defs>
                  <marker
                    id="arrow-head"
                    viewBox="0 0 10 10"
                    refX="18"
                    refY="5"
                    markerWidth="5"
                    markerHeight="5"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--c-accent)" />
                  </marker>
                  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>

                {/* Render Active Edges */}
                {visibleEdges.map((edge) => {
                  const sPos = nodePositionMap.get(edge.source)
                  const tPos = nodePositionMap.get(edge.target)
                  if (!sPos || !tPos) return null

                  const isNew = edge.introduced_at_step === currentStep

                  return (
                    <g key={edge.id} className={`edge-group ${isNew ? 'edge-just-added' : ''}`}>
                      <line
                        x1={sPos.x}
                        y1={sPos.y}
                        x2={tPos.x}
                        y2={tPos.y}
                        stroke={isNew ? 'var(--c-accent)' : 'var(--c-border-strong)'}
                        strokeWidth={isNew ? 2.2 : 1.2}
                        strokeDasharray={isNew ? '4 2' : 'none'}
                        markerEnd="url(#arrow-head)"
                        opacity={isNew ? 1 : 0.65}
                      />
                    </g>
                  )
                })}

                {/* Render Visible Nodes */}
                {visibleNodes.map((node) => {
                  const pos = nodePositionMap.get(node.id) || { x: 280, y: 200 }
                  const nx = pos.x
                  const ny = pos.y

                  const isRoot = node.id === timelineData?.all_nodes?.[0]?.id
                  const isRecent = node.introduced_at_step === currentStep
                  const isSelected = selectedNode?.id === node.id
                  const nodeColor = getSourceColor(node.source)

                  return (
                    <g
                      key={node.id}
                      className={`node-group ${isRecent ? 'node-pulse' : ''} ${isSelected ? 'node-selected' : ''}`}
                      transform={`translate(${nx}, ${ny})`}
                      onClick={() => setSelectedNode(node)}
                      style={{ cursor: 'pointer' }}
                    >
                      {/* Outer pulse ring for recent step addition */}
                      {isRecent && (
                        <circle
                          r={isRoot ? 24 : 18}
                          fill="none"
                          stroke={nodeColor}
                          strokeWidth="2"
                          className="pulse-ring"
                        />
                      )}

                      <circle
                        r={isRoot ? 18 : 13}
                        fill={isRoot ? 'var(--c-surface)' : 'var(--c-surface-2)'}
                        stroke={nodeColor}
                        strokeWidth={isRoot ? 2.5 : 1.8}
                        filter={isRecent || isSelected ? 'url(#glow)' : undefined}
                      />

                      <text
                        textAnchor="middle"
                        dy="3.5"
                        fontSize={isRoot ? '8.5' : '7'}
                        fontWeight="700"
                        fill="var(--c-text)"
                      >
                        {isRoot ? 'ROOT' : (node.source === 'github' ? 'PR' : (node.source === 'linear' ? 'ISSUE' : (node.source === 'slack' ? 'MSG' : 'NODE')))}
                      </text>

                      {/* Node Label underneath */}
                      <text
                        textAnchor="middle"
                        dy={isRoot ? '28' : '22'}
                        fontSize="8"
                        fontWeight="600"
                        fill="var(--c-text-2)"
                        className="node-svg-label"
                      >
                        {node.label.length > 12 ? `${node.label.slice(0, 10)}…` : node.label}
                      </text>
                    </g>
                  )
                })}
              </svg>
            </div>

            {/* Node Info Card / Legend */}
            <div className="graph-panel-footer">
              <div className="graph-legend">
                <span className="legend-item"><SlackIcon size={14} /> Slack</span>
                <span className="legend-item"><LinearIcon size={14} /> Linear</span>
                <span className="legend-item"><GitHubIcon size={14} /> GitHub</span>
                <span className="legend-item"><SourceIcon source="system" size={14} /> System Node</span>
              </div>

              {selectedNode && (
                <div className="selected-node-chip">
                  <span>Selected: <strong>{selectedNode.label}</strong> ({selectedNode.type})</span>
                  {onNavigateToTrace && (
                    <button
                      type="button"
                      className="chip-action-btn"
                      onClick={() => onNavigateToTrace(selectedNode.label)}
                    >
                      Trace Dependency →
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Chronological Event Stream */}
          <div className="timeline-events-panel">
            <div className="panel-header">
              <div className="panel-title">
                <span>INCIDENT EVENT STREAM</span>
                <span className="panel-badge">{events.length} Events Total</span>
              </div>
              <span className="live-pill">
                {currentStep >= events.length ? 'Timeline Complete' : `Active Step: #${currentStep}`}
              </span>
            </div>

            <div className="timeline-cards-list">
              {events.map((evt, idx) => {
                const stepNum = idx + 1
                const isActiveStep = stepNum === currentStep
                const isPastStep = stepNum < currentStep
                const isComplete = currentStep >= events.length

                return (
                  <div
                    key={evt.id}
                    ref={(el) => { eventCardsRef.current[stepNum] = el }}
                    className={`timeline-event-card ${isActiveStep ? 'card-active' : ''} ${isPastStep ? 'card-past' : ''} ${!isPastStep && !isActiveStep ? 'card-future' : ''} ${isComplete ? 'card-complete' : ''}`}
                    onClick={() => {
                      setIsPlaying(false)
                      setCurrentStep(stepNum)
                    }}
                  >
                    {/* Card Rail Anchor */}
                    <div className="card-rail">
                      <span className={`rail-node ${isActiveStep ? 'rail-active' : ''}`}>
                        {stepNum}
                      </span>
                      {stepNum < events.length && <span className="rail-line" />}
                    </div>

                    {/* Card Body */}
                    <div className="card-content">
                      <div className="card-meta-top">
                        <div className="meta-left">
                          <span className={`source-pill source-${evt.source}`}>
                            <SourceIcon source={evt.source} size={13} style={{ marginRight: 4 }} />
                            {evt.source.toUpperCase()} · {evt.channel_or_repo || evt.source_id}
                          </span>
                          <span className="delta-pill">{evt.relative_time}</span>
                        </div>
                        <span className={`phase-badge ${getPhaseBadgeClass(evt.phase)}`}>
                          {evt.phase_label}
                        </span>
                      </div>

                      <h3 className="card-title">{evt.title}</h3>
                      <p className="card-snippet">{evt.content_snippet}</p>

                      {evt.entities && evt.entities.length > 0 && (
                        <div className="card-entities-row">
                          <span className="entities-lbl">Entities:</span>
                          {[...new Set(evt.entities)].slice(0, 4).map((ent) => (
                            <span key={ent} className="card-entity-tag">{ent}</span>
                          ))}
                        </div>
                      )}

                      {/* Interactive Deep-Dive Actions */}
                      <div className="card-actions-row">
                        {evt.author && (
                          <span className="author-tag">
                            {evt.author}
                          </span>
                        )}
                        <div className="action-btns">
                          {onNavigateToAsk && (
                            <button
                              type="button"
                              className="card-cta-btn ask-cta"
                              onClick={(e) => {
                                e.stopPropagation()
                                onNavigateToAsk(`What happened in ${evt.title}?`)
                              }}
                              title={`Ask questions about ${evt.title}`}
                            >
                              Ask RAG →
                            </button>
                          )}
                          {onNavigateToTrace && (
                            <button
                              type="button"
                              className="card-cta-btn trace-cta"
                              onClick={(e) => {
                                e.stopPropagation()
                                onNavigateToTrace(evt.entities[0] || entity)
                              }}
                              title="Trace this component"
                            >
                              Trace Graph →
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Cypher Query Modal */}
      <CypherModal
        isOpen={showCypher}
        onClose={() => setShowCypher(false)}
        cypherInfo={timelineData?.cypher_inspection}
        title="Temporal Incident Replay — HydraDB OpenCypher Query"
      />
    </div>
  )
}
