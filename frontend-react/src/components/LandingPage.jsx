import React, { useState, useEffect } from "react"
import ThemeToggle from "./ThemeToggle.jsx"
import { isHydraOnline, getHydraStatusLabel, getHydraAriaLabel } from "../utils/hydraStatus.js"
import { QUOTA_STUDENT_MESSAGE, useQuota } from "../utils/quotaManager.js"
import { SourceIcon, SlackIcon, LinearIcon, GitHubIcon, JiraIcon, ConfluenceIcon, PagerDutyIcon } from "./SourceIcons.jsx"

function SignalFlowDiagram() {
  const [lit, setLit] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setLit(true), 600)
    return () => clearTimeout(t)
  }, [])
  const sources = [
    { id: "slack", label: "SLACK", excerpt: "\"Rollback discussion triggered by latency spike in eu-west.\"", ref: "#incidents" },
    { id: "linear", label: "LINEAR", excerpt: "REL-311 — Support ticket linking release notes and rollback alert.", ref: "ENG-8201" },
    { id: "github", label: "GITHUB", excerpt: "PR-99501 — Normalize function-invoke headers and retry logic.", ref: "PR-99501" },
  ]
  const outputs = ["REL-311", "api-search", "v3.1.1-legacy-tokenizer"]
  return (
    <div className={`lp-signal-flow${lit ? " lp-signal-flow--lit" : ""}`} aria-hidden="true">
      <div className="lp-sources">
        {sources.map((s, i) => (
          <div key={s.id} className="lp-source-card" style={{ animationDelay: `${i * 120}ms` }}>
            <div className="lp-source-label" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <SourceIcon source={s.id} size={14} />
              <span>{s.label}</span>
            </div>
            <div className="lp-source-ref">{s.ref}</div>
            <div className="lp-source-excerpt">{s.excerpt}</div>
          </div>
        ))}
      </div>
      <div className="lp-flow-connector">
        <svg viewBox="0 0 120 160" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0,27 Q60,27 60,80" stroke="rgba(232,162,71,0.22)" strokeWidth="1" fill="none" />
          <path d="M0,80 Q60,80 60,80" stroke="rgba(232,162,71,0.22)" strokeWidth="1" fill="none" />
          <path d="M0,133 Q60,133 60,80" stroke="rgba(232,162,71,0.22)" strokeWidth="1" fill="none" />
          <circle cx="60" cy="80" r="3" fill="var(--c-accent)" opacity="0.7" />
        </svg>
      </div>
      <div className="lp-central-node">
        <div className="lp-central-pulse" />
        <div className="lp-central-wordmark">VERIDEX</div>
        <div className="lp-central-sub">HydraDB Knowledge Graph</div>
      </div>
      <div className="lp-flow-connector lp-flow-connector--right">
        <svg viewBox="0 0 120 160" preserveAspectRatio="none" aria-hidden="true">
          <path d="M60,80 Q60,27 120,27" stroke="rgba(232,162,71,0.22)" strokeWidth="1" fill="none" />
          <path d="M60,80 Q60,80 120,80" stroke="rgba(232,162,71,0.22)" strokeWidth="1" fill="none" />
          <path d="M60,80 Q60,133 120,133" stroke="rgba(232,162,71,0.22)" strokeWidth="1" fill="none" />
          <circle cx="60" cy="80" r="3" fill="var(--c-accent)" opacity="0.7" />
        </svg>
      </div>
      <div className="lp-outputs">
        <div className="lp-output-label">RECONSTRUCTED STATE</div>
        {outputs.map((o, i) => (
          <div key={o} className="lp-output-entity" style={{ animationDelay: `${800 + i * 100}ms` }}>
            <span className="lp-output-dot" />
            {o}
          </div>
        ))}
        <div className="lp-output-meta-row">
          <span>Evidence</span>
          <span>Timeline</span>
          <span>Provenance</span>
        </div>
      </div>
    </div>
  )
}

function HeroLiveTerminalDesk({ onEnterConsole }) {
  const [typedQuery, setTypedQuery] = useState('')
  const [error, setError] = useState(null)
  const quota = useQuota()

  const quickQueries = [
    { label: 'INC-2026', q: 'What happened during incident INC-2026?' },
    { label: 'PR-99501', q: 'What changes were made in PR-99501?' },
    { label: 'REL-311', q: 'What happened with REL-311?' },
    { label: 'kernel-selector', q: 'What is kernel-selector about?' },
  ]

  const handleExecute = (targetQuery) => {
    if (quota.isExceeded) {
      setError(quota.studentMessage)
      return
    }
    onEnterConsole('ask', targetQuery)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleExecute(typedQuery.trim() || 'What happened during incident INC-2026?')
    }
  }

  return (
    <div className="lp-hero-live-desk">
      <div className="lp-terminal-bar">
        <span className="lp-terminal-dot" />
        <span className="lp-terminal-path">veridex://hydradb/enterprise-rag/live</span>
        <span className="lp-terminal-status">
          {quota.isExceeded
            ? (quota.stage >= 2 ? 'DEMO LIMIT REACHED' : 'QUOTA LIMIT REACHED — REFRESH TO EXTEND')
            : `DEMO QUOTA: ${quota.remaining}/${quota.maxQuota} LEFT`}
        </span>
      </div>

      {(quota.isExceeded || error) && (
        <div className="quota-student-banner" style={{ margin: '12px 14px 0 14px' }} role="alert">
          <span className="quota-student-icon" aria-hidden="true">💡</span>
          <span className="quota-student-text">{error || quota.studentMessage}</span>
        </div>
      )}

      <div className="lp-hero-inline-query">
        <span className="lp-prompt-symbol">&gt;</span>
        <input
          type="text"
          className="lp-terminal-input"
          placeholder="Ask a question or enter PR/incident ID (e.g. 'What caused INC-2026?')..."
          value={typedQuery}
          onChange={(e) => setTypedQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Direct query input from hero"
        />
        <button
          className="lp-btn-primary"
          onClick={() => handleExecute(typedQuery.trim() || 'What happened during incident INC-2026?')}
          type="button"
          id="lp-hero-execute-direct"
        >
          INVESTIGATE [↵]
        </button>
      </div>
      <div className="lp-terminal-quick-queries">
        <span className="lp-tq-label">Quick query:</span>
        {quickQueries.map((item) => (
          <button
            key={item.label}
            className="lp-tq-btn"
            onClick={() => handleExecute(item.q)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function JudgeQuickGuideSection({ onEnterConsole }) {
  return (
    <section className="lp-section lp-judge-section" aria-labelledby="judge-guide-heading">
      <div className="lp-container">
        <div className="lp-judge-guide-header">
          <div className="lp-judge-badge-row">
            <span className="lp-judge-badge">JUDGE &amp; EVALUATOR QUICK START</span>
            <span className="lp-judge-track-badge">HACK HYDRA 2026 · TRACK 1: ENTERPRISE CONTEXT</span>
          </div>
          <h2 className="lp-section-title" id="judge-guide-heading">
            5 ways to evaluate Veridex in 60 seconds.
          </h2>
          <p className="lp-section-body">
            Veridex merges fragmented Slack incident chatter, Linear tickets, GitHub pull requests, Jira tickets, and Confluence RFCs into a deterministic bi-temporal knowledge graph hosted on <strong>HydraDB Cloud v2</strong>. Here is the recommended evaluation sequence:
          </p>
        </div>

        <div className="lp-judge-steps-list">
          {/* STEP 1: ASK */}
          <div className="lp-judge-step-row">
            <div className="lp-judge-step-num-col">
              <span className="lp-judge-step-num">01</span>
              <span className="step-tag ask">GROUNDED RAG</span>
            </div>
            <div className="lp-judge-step-content-col">
              <h3 className="lp-judge-step-title">Ask natural language questions</h3>
              <p className="lp-judge-step-desc">
                HydraDB extracts the bounded evidence subgraph [E1, E2] with zero hallucinated links and zero vector drift.
              </p>
            </div>
            <div className="lp-judge-step-action-col">
              <div className="lp-judge-test-box">
                <span className="test-lbl">RECOMMENDED TEST:</span>
                <button
                  type="button"
                  className="lp-judge-action-btn ask-btn"
                  onClick={() => onEnterConsole('ask', 'What happened during incident INC-2026?')}
                >
                  Ask: &ldquo;What happened in INC-2026?&rdquo; →
                </button>
              </div>
              <div className="lp-judge-alt-presets">
                <span className="alt-lbl">Also try:</span>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('ask', 'What changes were made in PR-99501?')}>PR-99501</button>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('ask', 'What caused the cross-region KMS timeouts in JIRA-4029?')}>JIRA-4029</button>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('ask', 'What architectural decisions were approved in RFC-881 ADR?')}>RFC-881</button>
              </div>
            </div>
          </div>

          {/* STEP 2: TRACE */}
          <div className="lp-judge-step-row">
            <div className="lp-judge-step-num-col">
              <span className="lp-judge-step-num">02</span>
              <span className="step-tag trace">DEPENDENCY GRAPH</span>
            </div>
            <div className="lp-judge-step-content-col">
              <h3 className="lp-judge-step-title">Trace blast radius &amp; relationships</h3>
              <p className="lp-judge-step-desc">
                Traverse 1–3 hop BFS causal dependencies across microservices, pull requests, Jira tickets, and on-call alerts.
              </p>
            </div>
            <div className="lp-judge-step-action-col">
              <div className="lp-judge-test-box">
                <span className="test-lbl">RECOMMENDED TEST:</span>
                <button
                  type="button"
                  className="lp-judge-action-btn trace-btn"
                  onClick={() => onEnterConsole('trace', 'PR-99501')}
                >
                  Trace: &ldquo;PR-99501&rdquo; Blast Radius →
                </button>
              </div>
              <div className="lp-judge-alt-presets">
                <span className="alt-lbl">Also try:</span>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('trace', 'INC-2026')}>INC-2026</button>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('trace', 'JIRA-4029')}>JIRA-4029</button>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('trace', 'RFC-881')}>RFC-881</button>
              </div>
            </div>
          </div>

          {/* STEP 3: TIMELINE REPLAY */}
          <div className="lp-judge-step-row featured">
            <div className="lp-judge-step-num-col">
              <span className="lp-judge-step-num">03</span>
              <span className="step-tag timeline">TIME-TRAVEL REPLAY</span>
            </div>
            <div className="lp-judge-step-content-col">
              <h3 className="lp-judge-step-title">Scrub through incident evolution</h3>
              <p className="lp-judge-step-desc">
                VCR player scrubbing through Detection → Investigation → Mitigation → Resolution phases.
              </p>
            </div>
            <div className="lp-judge-step-action-col">
              <div className="lp-judge-test-box">
                <span className="test-lbl">RECOMMENDED TEST:</span>
                <button
                  type="button"
                  className="lp-judge-action-btn timeline-btn"
                  onClick={() => onEnterConsole('timeline', 'INC-2026')}
                >
                  Launch: &ldquo;INC-2026&rdquo; Replay Player →
                </button>
              </div>
              <div className="lp-judge-alt-presets">
                <span className="alt-lbl">Also try:</span>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('timeline', 'REL-311')}>REL-311 (Rollback)</button>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('timeline', 'PR-99501')}>PR-99501 (Hotfix)</button>
              </div>
            </div>
          </div>

          {/* STEP 4: CONFLICT RESOLUTION */}
          <div className="lp-judge-step-row">
            <div className="lp-judge-step-num-col">
              <span className="lp-judge-step-num">04</span>
              <span className="step-tag conflicts">TRUTH ARBITER</span>
            </div>
            <div className="lp-judge-step-content-col">
              <h3 className="lp-judge-step-title">Resolve cross-source contradictions</h3>
              <p className="lp-judge-step-desc">
                Determine canonical ground truth between Slack triage panic, Linear tickets, and merged GitHub code.
              </p>
            </div>
            <div className="lp-judge-step-action-col">
              <div className="lp-judge-test-box">
                <span className="test-lbl">RECOMMENDED TEST:</span>
                <button
                  type="button"
                  className="lp-judge-action-btn conflicts-btn"
                  onClick={() => onEnterConsole('conflicts', '')}
                >
                  Open Conflict Arbiter →
                </button>
              </div>
              <div className="lp-judge-alt-presets">
                <span className="alt-lbl">Inspect:</span>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('conflicts', 'INC-2026')}>INC-2026</button>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('conflicts', 'Bluecrest')}>Bluecrest</button>
                <button type="button" className="alt-chip" onClick={() => onEnterConsole('conflicts', 'REL-311')}>REL-311</button>
              </div>
            </div>
          </div>

          {/* STEP 5: GRAPH CANVAS EXPLORER */}
          <div className="lp-judge-step-row">
            <div className="lp-judge-step-num-col">
              <span className="lp-judge-step-num">05</span>
              <span className="step-tag" style={{ background: 'rgba(6, 182, 212, 0.12)', color: '#0891b2', border: '1px solid rgba(6, 182, 212, 0.3)' }}>GRAPH CANVAS</span>
            </div>
            <div className="lp-judge-step-content-col">
              <h3 className="lp-judge-step-title">Interactive knowledge topology</h3>
              <p className="lp-judge-step-desc">
                Full-screen interactive canvas with pan, zoom, node drag, relationship filters, and multi-source inspection.
              </p>
            </div>
            <div className="lp-judge-step-action-col">
              <div className="lp-judge-test-box">
                <span className="test-lbl">RECOMMENDED TEST:</span>
                <button
                  type="button"
                  className="lp-judge-action-btn"
                  style={{ background: '#0891b2', color: '#ffffff' }}
                  onClick={() => onEnterConsole('graph', '')}
                >
                  Launch: Knowledge Graph Canvas →
                </button>
              </div>
              <div className="lp-judge-alt-presets">
                <span className="alt-lbl">Sources:</span>
                <span className="alt-chip">Jira</span>
                <span className="alt-chip">Confluence</span>
                <span className="alt-chip">GitHub</span>
                <span className="alt-chip">Slack</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function TimelineShowcaseSection({ onEnterConsole }) {
  const phases = [
    { icon: '01', label: 'Detection', desc: 'PagerDuty alerts, anomaly telemetry, and Slack error spikes' },
    { icon: '02', label: 'Investigation', desc: 'Linear tickets, triage coordination, and root-cause hypothesis' },
    { icon: '03', label: 'Mitigation', desc: 'Hotfix PRs, fallback flag flips, and canary deployments' },
    { icon: '04', label: 'Resolution', desc: 'Service recovery, metric stabilization, and post-mortem closure' },
  ]

  return (
    <section className="lp-section lp-section--ruled" aria-labelledby="timeline-showcase-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="timeline-showcase-heading">BI-TEMPORAL REASONING ON HYDRADB</div>
        <h2 className="lp-section-title">Incidents unfold over time. Replay every step.</h2>
        <p className="lp-section-body">
          Traditional vector stores only see a static snapshot of documents. Veridex leverages HydraDB&apos;s bi-temporal knowledge graph structure to reconstruct discrete time states ($T_0 \rightarrow T_n$), giving incident response teams complete causal clarity.
        </p>

        <div className="lp-timeline-showcase-card">
          <div className="lp-timeline-phases-row">
            {phases.map((p, idx) => (
              <div key={p.label} className="lp-timeline-phase-box">
                <div className="phase-icon-badge">{p.icon}</div>
                <div className="phase-title">{p.label}</div>
                <div className="phase-desc">{p.desc}</div>
                {idx < phases.length - 1 && <span className="phase-arrow" aria-hidden="true">→</span>}
              </div>
            ))}
          </div>

          <div className="lp-timeline-preview-desk">
            <div className="preview-top-bar">
              <div className="preview-meta">
                <span className="live-dot" />
                <span>FEATURED REPLAY: <strong>INC-2026</strong> (GPU Pool Queue Exceeded)</span>
                <span className="badge-pill">7 Events · 4 Sources</span>
              </div>
              <button
                type="button"
                className="lp-btn-primary lp-btn-sm"
                onClick={() => onEnterConsole('timeline', 'INC-2026')}
              >
                OPEN TIMELINE PLAYER
              </button>
            </div>
            <div className="preview-scrubber-sim">
              <div className="sim-rail">
                <span className="sim-node active">T+0m (Alert)</span>
                <span className="sim-line" />
                <span className="sim-node active">T+18m (Triage)</span>
                <span className="sim-line" />
                <span className="sim-node active">T+42m (Fix PR)</span>
                <span className="sim-line" />
                <span className="sim-node active">T+1h 15m (Canary)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function ConflictResolverShowcaseSection({ onEnterConsole }) {
  return (
    <section className="lp-section lp-section--ruled" aria-labelledby="conflicts-showcase-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="conflicts-showcase-heading">TRACK 01: ONTOLOGY ALIGNMENT &amp; CONFLICT RESOLUTION</div>
        <h2 className="lp-section-title">Contradictory chat panic vs. code ground truth. Resolved deterministically.</h2>
        <p className="lp-section-body">
          During production outages, enterprise communications contain contradictory noise: triage Slack channels post unverified guesses, Linear tickets reference stale configurations, and GitHub pull requests contain the true hotfix. Traditional vector RAG blends conflicting text chunks indiscriminately. Veridex evaluates source authority and bi-temporal graph paths in HydraDB to establish canonical ground truth.
        </p>

        <div className="lp-conflicts-showcase-card">
          <div className="lp-conflicts-hierarchy-bar">
            <span className="hierarchy-title">ONTOLOGICAL AUTHORITY HIERARCHY:</span>
            <div className="hierarchy-pills">
              <span className="h-pill git"><GitHubIcon size={12} /> Merged GitHub PR / Code (0.95–0.98)</span>
              <span className="h-arrow">›</span>
              <span className="h-pill linear"><LinearIcon size={12} /> Linear Resolved Ticket (0.75–0.88)</span>
              <span className="h-arrow">›</span>
              <span className="h-pill slack"><SlackIcon size={12} /> Ephemeral Slack Chat (0.45–0.60)</span>
            </div>
          </div>

          <div className="lp-conflicts-preview-grid">
            <div className="preview-truth-box">
              <div className="preview-truth-header">
                <div className="preview-header-left">
                  <span className="truth-dot" />
                  <span className="truth-title">CANONICAL GROUND TRUTH (WINNER)</span>
                </div>
                <span className="truth-badge">Authority: 98%</span>
              </div>
              <p className="preview-truth-text">
                &ldquo;Root cause was kernel-selector v2.1.0 cgroup memory exhaustion under peak concurrency, resolved by emergency hotfix PR-99501.&rdquo;
              </p>
              <div className="preview-truth-meta">
                <span className="source-tag git"><GitHubIcon size={12} /> PR-99501 (Merged commit d4f881a)</span>
                <span className="time-tag">2026-02-14 09:34 UTC</span>
              </div>
            </div>

            <div className="preview-superseded-box">
              <div className="preview-superseded-header">
                <div className="preview-header-left">
                  <span className="superseded-dot" />
                  <span className="superseded-title">SUPERSEDED / REFUTED CLAIM</span>
                </div>
                <span className="superseded-badge">Refuted</span>
              </div>
              <p className="preview-superseded-text">
                &ldquo;Incident was caused by transient AWS us-east-1 network partition, waiting for AWS status page update.&rdquo;
              </p>
              <div className="preview-superseded-meta">
                <span className="source-tag slack"><SlackIcon size={12} /> Slack #incidents (msg_8537794)</span>
                <span className="refute-reason">Disproved by memory profiling</span>
              </div>
            </div>
          </div>

          <div className="lp-conflicts-action-bar">
            <div className="action-bar-left">
              <span className="cypher-feature-tag">HYDRADB OPENCYPHER QUERY INSPECTOR INCLUDED</span>
              <span className="cypher-feature-desc">Inspect exact OpenCypher graph traversals and why Vector RAG fails on each query.</span>
            </div>
            <button
              type="button"
              className="lp-btn-primary lp-btn-sm"
              onClick={() => onEnterConsole('conflicts', '')}
            >
              OPEN CONFLICT ARBITER →
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}

function GraphCanvasShowcaseSection({ onEnterConsole }) {
  return (
    <section className="lp-section lp-section--ruled" aria-labelledby="graph-showcase-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="graph-showcase-heading">TRACK 01: EXTENDED ADAPTERS &amp; KNOWLEDGE GRAPH CANVAS EXPLORER</div>
        <h2 className="lp-section-title">Full-screen interactive topology across Slack, Linear, GitHub, Jira &amp; Confluence.</h2>
        <p className="lp-section-body">
          Explore complete enterprise multi-hop dependency graphs with smooth zoom, pan, and live node dragging. Inspect typed relationships (<code>[:CAUSED_BY]</code>, <code>[:RESOLVES]</code>, <code>[:STANDARDIZES]</code>, <code>[:DEPENDS_ON]</code>) across 6 canonical enterprise source systems with zero vector hallucinations.
        </p>

        <div className="lp-timeline-showcase-card">
          <div className="lp-conflicts-hierarchy-bar">
            <span className="hierarchy-title">SUPPORTED ENTERPRISE DATA SOURCES:</span>
            <div className="hierarchy-pills">
              <span className="h-pill git"><GitHubIcon size={12} /> GitHub PRs &amp; Commits</span>
              <span className="h-arrow">·</span>
              <span className="h-pill linear"><LinearIcon size={12} /> Linear Issues</span>
              <span className="h-arrow">·</span>
              <span className="h-pill slack"><SlackIcon size={12} /> Slack Incidents</span>
              <span className="h-arrow">·</span>
              <span className="h-pill" style={{ background: 'rgba(38, 132, 255, 0.12)', color: '#0052cc', border: '1px solid rgba(38, 132, 255, 0.3)' }}><JiraIcon size={12} /> Jira Tickets</span>
              <span className="h-arrow">·</span>
              <span className="h-pill" style={{ background: 'rgba(0, 82, 204, 0.12)', color: '#0052cc', border: '1px solid rgba(0, 82, 204, 0.3)' }}><ConfluenceIcon size={12} /> Confluence RFCs</span>
              <span className="h-arrow">·</span>
              <span className="h-pill" style={{ background: 'rgba(245, 158, 11, 0.12)', color: '#b45309', border: '1px solid rgba(245, 158, 11, 0.3)' }}><PagerDutyIcon size={12} /> PagerDuty Alerts</span>
            </div>
          </div>

          <div className="preview-scrubber-sim">
            <div className="sim-rail">
              <span className="sim-node active">INC-2026</span>
              <span className="sim-line" />
              <span className="sim-node active">kernel-selector</span>
              <span className="sim-line" />
              <span className="sim-node active">PR-99501</span>
              <span className="sim-line" />
              <span className="sim-node active">JIRA-4029</span>
              <span className="sim-line" />
              <span className="sim-node active">RFC-881 ADR</span>
            </div>
          </div>

          <div className="lp-conflicts-action-bar">
            <div className="action-bar-left">
              <span className="cypher-feature-tag" style={{ background: 'rgba(6, 182, 212, 0.12)', color: '#0891b2', borderColor: 'rgba(6, 182, 212, 0.3)' }}>CANVAS CONTROLS: ZOOM · PAN · DRAG · RELATIONSHIP FILTER</span>
              <span className="cypher-feature-desc">Interactive physics graph with node inspection drawer and 1-click RAG jumps.</span>
            </div>
            <button
              type="button"
              className="lp-btn-primary lp-btn-sm"
              onClick={() => onEnterConsole('graph', '')}
            >
              OPEN GRAPH CANVAS →
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}

function WorkflowStepsSection() {
  const steps = [
    {
      step: "01",
      title: "EXTRACT & INDEX",
      headline: "Multi-source canonical ingestion.",
      desc: "Ingests unstructured Slack incident threads, Linear tickets, and GitHub pull requests into typed statements with stable alias resolution.",
    },
    {
      step: "02",
      title: "DETERMINISTIC TRAVERSAL",
      headline: "Multi-hop graph resolution in HydraDB.",
      desc: "Traverses real entity relationships and extracts bounded evidence bundles with strict message and document IDs—zero vector drift.",
    },
    {
      step: "03",
      title: "GROUNDED SYNTHESIS",
      headline: "Strict citation-backed answers.",
      desc: "Gemini synthesizes verifiable conclusions restricted exclusively to the retrieved graph bundle [E1, E2], with zero hallucinated links.",
    },
  ]

  return (
    <section className="lp-section" aria-labelledby="workflow-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="workflow-heading">GRAPH REASONING ARCHITECTURE</div>
        <h2 className="lp-section-title">Deterministic graph traversal. Zero-hallucination synthesis.</h2>
        <p className="lp-section-body">
          Traditional vector RAG fails on relational causality. Veridex separates structural graph resolution in HydraDB from language generation.
        </p>
        <div className="lp-workflow-grid">
          {steps.map((s) => (
            <div key={s.step} className="lp-workflow-card">
              <div className="lp-workflow-num">{s.step}</div>
              <div className="lp-workflow-tag">{s.title}</div>
              <h3 className="lp-workflow-headline">{s.headline}</h3>
              <p className="lp-workflow-desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function AskVsTraceSection({ onEnterConsole }) {
  return (
    <section className="lp-section lp-section--ruled" aria-labelledby="comparison-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="comparison-heading">TWO COMPLEMENTARY MODES</div>
        <h2 className="lp-section-title">Choose your investigation lens: Ask or Trace.</h2>
        <p className="lp-section-body">
          Whether you need a direct evidence-backed answer to an incident question or want to map multi-hop component dependencies, Veridex provides dedicated workflows.
        </p>

        <div className="lp-comparison-grid">
          {/* ASK CARD */}
          <div className="lp-comparison-card">
            <div className="lp-comparison-header">
              <div className="lp-comparison-badge ask">ASK MODE</div>
              <h3 className="lp-comparison-title">Get an evidence-backed answer.</h3>
            </div>
            <p className="lp-comparison-desc">
              Ask natural language questions about incidents, tickets, PRs, and team decisions. Veridex returns a grounded answer strictly citing retrieved graph evidence.
            </p>
            <div className="lp-comparison-example">
              <div className="lp-comparison-ex-lbl">EXAMPLE QUESTION</div>
              <div className="lp-comparison-ex-val">&ldquo;What happened during incident INC-2026?&rdquo;</div>
            </div>
            <ul className="lp-comparison-features">
              <li><span>✓</span> Grounded answer language synthesis</li>
              <li><span>✓</span> Bounded evidence bundle [E1, E2, ...]</li>
              <li><span>✓</span> Direct source document and message provenance</li>
              <li><span>✓</span> Discovered entity shortcuts for follow-up tracing</li>
            </ul>
            <div className="lp-comparison-action">
              <button
                className="lp-btn-primary"
                onClick={() => onEnterConsole("ask")}
                id="lp-ask-mode-cta"
                type="button"
              >
                ASK A QUESTION →
              </button>
            </div>
          </div>

          {/* TRACE CARD */}
          <div className="lp-comparison-card">
            <div className="lp-comparison-header">
              <div className="lp-comparison-badge trace">TRACE MODE</div>
              <h3 className="lp-comparison-title">Understand what is connected.</h3>
            </div>
            <p className="lp-comparison-desc">
              Enter any technical entity, ticket, or pull request to traverse multi-hop relationships, reveal affected components, and view a reconstructed timeline.
            </p>
            <div className="lp-comparison-example">
              <div className="lp-comparison-ex-lbl">EXAMPLE ENTITY</div>
              <div className="lp-comparison-ex-val">&ldquo;PR-99501&rdquo; or &ldquo;INC-2026&rdquo;</div>
            </div>
            <ul className="lp-comparison-features">
              <li><span>✓</span> Multi-hop BFS dependency graph traversal (1–3 hops)</li>
              <li><span>✓</span> Upstream causes and downstream affected components</li>
              <li><span>✓</span> Chronological statement timeline with timestamps</li>
              <li><span>✓</span> Zero-hallucination graph connectivity</li>
            </ul>
            <div className="lp-comparison-action">
              <button
                className="lp-btn-ghost"
                onClick={() => onEnterConsole("trace")}
                id="lp-trace-mode-cta"
                type="button"
              >
                TRACE DEPENDENCIES →
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function SignalsToStateSection() {
  const sources = [
    { key: "slack", label: "SLACK", desc: "Conversations and incident discussions", items: ["#incidents", "#eng-runtime", "#devex"] },
    { key: "linear", label: "LINEAR", desc: "Issues and engineering work", items: ["ENG-8201", "REL-311", "DES-23981"] },
    { key: "github", label: "GITHUB", desc: "Pull requests and implementation changes", items: ["PR-99501", "PR-35802", "PR-209876"] },
  ]
  return (
    <section className="lp-section lp-section--ruled" aria-labelledby="signals-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="signals-heading">FROM SIGNALS TO STATE</div>
        <h2 className="lp-section-title">Three sources. One coherent graph.</h2>
        <p className="lp-section-body">Slack threads, Linear issues, and GitHub pull requests each capture a fragment of the truth. Veridex merges them through HydraDB into a queryable, traceable knowledge structure.</p>
        <div className="lp-signals-layout">
          <div className="lp-signal-sources">
            {sources.map((s) => (
              <div key={s.key} className="lp-signal-source">
                <div className="lp-signal-source-header">
                  <span className="lp-signal-source-name" style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <SourceIcon source={s.key} size={15} />
                    <span>{s.label}</span>
                  </span>
                  <span className="lp-signal-source-desc">{s.desc}</span>
                </div>
                <div className="lp-signal-items">
                  {s.items.map((item) => (<span key={item} className="lp-signal-item">{item}</span>))}
                </div>
              </div>
            ))}
          </div>
          <div className="lp-signals-arrow" aria-hidden="true">
            <div className="lp-signals-arrow-line" />
            <div className="lp-signals-arrow-label">HydraDB MERGE</div>
            <div className="lp-signals-arrow-line" />
          </div>
          <div className="lp-reconstructed">
            <div className="lp-reconstructed-header">VERIDEX GRAPH</div>
            <div className="lp-reconstructed-entities">
              {["REL-311", "api-search", "v3.1.1-legacy-tokenizer"].map((e) => (
                <div key={e} className="lp-recon-entity">{e}</div>
              ))}
            </div>
            <div className="lp-reconstructed-dims">
              <span>Evidence</span><span>Timeline</span><span>Dependencies</span><span>Provenance</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function InvestigationExample({ onEnterConsole }) {
  const evidence = [
    { id: "E1", entity: "REL-311", type: "fact", statement: "Support ticket REL-311 has been created, linking release notes, and is set to alert support if a rollback occurs.", msg: "8537794879600693670" },
    { id: "E2", entity: "REL-311", type: "fact", statement: "A monitor snapshot of eu-west showed error_rate=1.1%, p95_latency=4800ms, linked to REL-311 release window.", msg: "8537794879600693670" },
  ]
  const [activeEvidence, setActiveEvidence] = useState(null)
  const toggle = (id) => setActiveEvidence(activeEvidence === id ? null : id)
  return (
    <section className="lp-section" aria-labelledby="example-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="example-heading">INVESTIGATION EXAMPLE</div>
        <h2 className="lp-section-title">See a real query in action.</h2>
        <p className="lp-section-body">This example uses real entities extracted from the Veridex knowledge graph. Not simulated data.</p>
        <div className="lp-example-block">
          <div className="lp-example-query">
            <div className="lp-example-query-label">QUESTION</div>
            <div className="lp-example-query-text">"What happened with REL-311?"</div>
          </div>
          <div className="lp-example-answer">
            <div className="lp-example-answer-header">
              <span className="lp-example-answer-label">GROUNDED SYNTHESIS</span>
              <span className="lp-grounded-badge"><span className="lp-grounded-dot" />GROUNDED</span>
            </div>
            <div className="lp-example-answer-body">
              Support ticket REL-311 has been created, linking release notes, and is set to alert support if a rollback occurs.{" "}
              {evidence.map((e) => (
                <button key={e.id} className={`lp-citation-pill${activeEvidence === e.id ? " active" : ""}`} onClick={() => toggle(e.id)} aria-pressed={activeEvidence === e.id}>{e.id}</button>
              ))}
            </div>
          </div>
          <div className="lp-example-evidence">
            <div className="lp-example-evidence-label">EVIDENCE BUNDLE</div>
            {evidence.map((e) => (
              <div key={e.id} className={`lp-example-evidence-row${activeEvidence === e.id ? " lp-example-evidence-row--highlighted" : ""}`} role="button" tabIndex={0} onClick={() => toggle(e.id)} onKeyDown={(ev) => ev.key === "Enter" && toggle(e.id)}>
                <div className="lp-example-eid">{e.id}</div>
                <div className="lp-example-econtent">
                  <div className="lp-example-emeta">
                    <span className="lp-example-entity">{e.entity}</span>
                    <span className={`type-badge ${e.type}`}>{e.type.toUpperCase()}</span>
                  </div>
                  <div className="lp-example-etext">{e.statement}</div>
                  <div className="lp-example-eprov">msg:{e.msg}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="lp-example-cta">
            <button className="lp-btn-primary" onClick={onEnterConsole} id="lp-example-open-console">RUN A REAL INVESTIGATION</button>
          </div>
        </div>
      </div>
    </section>
  )
}

function DependencyTracePreview() {
  const entities = [
    { name: "REL-311", root: true },
    { name: "api-search", root: false },
    { name: "v3.1.1-legacy-tokenizer", root: false },
    { name: "v3.1.1-legacy-tokenizer pinned to 1%", root: false },
  ]
  const timeline = [
    { n: "01", type: "FACT", label: "Monitor snapshot", text: "eu-west error_rate=1.1%, p95_latency=4800ms" },
    { n: "02", type: "ACTION", label: "Variant test", text: "Omar running targeted variant test with v3.1.1-legacy-tokenizer" },
    { n: "03", type: "FACT", label: "Support ticket", text: "REL-311 created, linking release notes and rollback alert" },
    { n: "04", type: "ACTION", label: "Route decision", text: "Team reconvenes in 12 min; legacy-tokenizer test determines rollback" },
  ]
  return (
    <section className="lp-section lp-section--ruled" aria-labelledby="trace-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="trace-heading">DEPENDENCY TRACE</div>
        <h2 className="lp-section-title">Not just an answer. A dependency map.</h2>
        <p className="lp-section-body">Veridex traverses the graph to reveal how entities relate across conversations, issues, and commits. Every hop is grounded in provenance.</p>
        <div className="lp-trace-layout">
          <div className="lp-trace-graph">
            <div className="lp-trace-graph-label">DEPENDENCY GRAPH</div>
            <div className="lp-trace-entities">
              {entities.map((e, i) => (
                <React.Fragment key={e.name}>
                  {i > 0 && <div className="lp-trace-arrow">&#8595;</div>}
                  <div className={`lp-trace-entity${e.root ? " lp-trace-entity--root" : ""}`}>{e.name}</div>
                </React.Fragment>
              ))}
            </div>
          </div>
          <div className="lp-trace-timeline">
            <div className="lp-trace-graph-label">RECONSTRUCTED TIMELINE</div>
            {timeline.map((t) => (
              <div key={t.n} className="lp-trace-timeline-row">
                <div className="lp-trace-timeline-n">{t.n}</div>
                <div className="lp-trace-timeline-content">
                  <div className="lp-trace-timeline-meta">
                    <span className={`type-badge ${t.type.toLowerCase()}`}>{t.type}</span>
                    <span className="lp-trace-timeline-lbl">{t.label}</span>
                  </div>
                  <div className="lp-trace-timeline-text">{t.text}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

function WhyHydraSection({ onNavigateToWhyHydra }) {
  const steps = [
    { label: "Raw Enterprise Signals", desc: "Slack, Linear, GitHub" },
    { label: "Semantic Extraction", desc: "Gemini extracts typed facts, actions, decisions" },
    { label: "HydraDB Graph", desc: "Deterministic structural + semantic graph layer" },
    { label: "Deterministic Retrieval", desc: "Graph-aware traversal — no vector approximation" },
    { label: "Evidence Bundle", desc: "Bounded, provenance-preserving evidence set" },
    { label: "Gemini Synthesis", desc: "Language synthesis only from the evidence bundle" },
  ]
  return (
    <section className="lp-section" aria-labelledby="why-hydra-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="why-hydra-heading">WHY HYDRADB</div>
        <h2 className="lp-section-title">HydraDB handles the graph.<br />Gemini handles the language.</h2>
        <p className="lp-section-body">Traditional RAG architectures approximate retrieval with vector similarity. Veridex uses HydraDB's graph-aware retrieval layer to resolve relationships and provenance before synthesis begins. Graph reasoning and language generation are strictly separated.</p>
        <div className="lp-arch-pipeline">
          {steps.map((s, i) => (
            <React.Fragment key={s.label}>
              <div className="lp-arch-step">
                <div className="lp-arch-step-n">{String(i + 1).padStart(2, "0")}</div>
                <div className="lp-arch-step-content">
                  <div className="lp-arch-step-label">{s.label}</div>
                  <div className="lp-arch-step-desc">{s.desc}</div>
                </div>
              </div>
              {i < steps.length - 1 && <div className="lp-arch-pipe-arrow" aria-hidden="true">&#8595;</div>}
            </React.Fragment>
          ))}
        </div>
        <div className="lp-arch-cta">
          <button className="lp-btn-ghost" onClick={onNavigateToWhyHydra} id="lp-explore-arch-btn">HOW VERIDEX WORKS &#8594;</button>
        </div>
      </div>
    </section>
  )
}

export default function LandingPage({ onEnterConsole, onNavigateToWhyHydra, hydraStatus, theme, onToggleTheme }) {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])
  const isOnline = isHydraOnline(hydraStatus)
  return (
    <div className="lp-root">
      {/* Announcement Ribbon (navbar.gallery) */}
      <div className="lp-announcement-bar">
        <span className="lp-announcement-pill">HACK HYDRA 2026</span>
        <span className="lp-announcement-text">Track 1: Enterprise Context &amp; Ontology — Live on HydraDB Cloud</span>
        <span className="lp-announcement-sep" aria-hidden="true">&#183;</span>
        <a
          href="https://github.com/toufiqfarhan0/deptrace"
          target="_blank"
          rel="noopener noreferrer"
          className="lp-announcement-github-link"
          aria-label="View source repository on GitHub"
        >
          <GitHubIcon size={12} />
          <span>GitHub Repo &#8599;</span>
        </a>
      </div>

      <header className={`lp-nav${scrolled ? " lp-nav--scrolled" : ""}`} role="banner">
        <div className="lp-nav-inner">
          <div className="lp-nav-wordmark">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--c-accent)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
              <circle cx="5" cy="5" r="2.5" fill="var(--c-accent)"/>
              <circle cx="19" cy="5" r="2.5" fill="var(--c-accent)"/>
              <circle cx="19" cy="19" r="2.5" fill="var(--c-accent)"/>
              <path d="M7.5 5h9M19 7.5v9"/>
            </svg>
            <span className="lp-nav-logo">VERIDEX</span>
          </div>
          <nav className="lp-nav-links" aria-label="Product navigation">
            <button className="lp-nav-link" onClick={() => onEnterConsole("ask")} id="lp-nav-investigate">ASK</button>
            <button className="lp-nav-link" onClick={() => onEnterConsole("trace")} id="lp-nav-trace">TRACE</button>
            <button className="lp-nav-link" onClick={() => onEnterConsole("timeline")} id="lp-nav-timeline">TIMELINE</button>
            <button className="lp-nav-link" onClick={() => onEnterConsole("suggestions")} id="lp-nav-suggestions">SUGGESTIONS</button>
            <button className="lp-nav-link" onClick={() => onEnterConsole("entities")} id="lp-nav-explore">ENTITIES</button>
            <button className="lp-nav-link" onClick={onNavigateToWhyHydra} id="lp-nav-why">HOW IT WORKS</button>
          </nav>
          <div className="lp-nav-right">
            {theme && onToggleTheme && (
              <ThemeToggle theme={theme} onToggleTheme={onToggleTheme} />
            )}
            <div
              className="lp-nav-status"
              role="status"
              aria-label={getHydraAriaLabel(hydraStatus)}
            >
              <span className={`lp-nav-status-dot${isOnline ? " lp-nav-status-dot--ok" : ""}`} />
              <span>{getHydraStatusLabel(hydraStatus, { format: "landing" })}</span>
            </div>
            <a
              href="https://github.com/toufiqfarhan0/deptrace"
              target="_blank"
              rel="noopener noreferrer"
              className="lp-nav-github-btn"
              id="lp-nav-view-code"
              title="View source code on GitHub"
              aria-label="View source code on GitHub"
            >
              <GitHubIcon size={14} />
              <span>VIEW CODE</span>
            </a>
            <button className="lp-btn-primary lp-btn-sm" onClick={() => onEnterConsole("ask")} id="lp-nav-open-console">OPEN CONSOLE</button>
          </div>
        </div>
      </header>

      <section className="lp-hero" aria-labelledby="hero-heading">
        <div className="lp-hero-inner">
          <div className="lp-hero-left">
            <div className="lp-hero-eyebrow">EVIDENCE-FIRST KNOWLEDGE INVESTIGATION</div>
            <h1 className="lp-hero-headline" id="hero-heading">
              Search your company{"\u2019"}s technical truth with <span className="lp-hero-accent">guaranteed provenance.</span>
            </h1>
            <p className="lp-hero-body">
              Ask questions about incidents, tickets, pull requests, and engineering decisions. Veridex traverses HydraDB knowledge graph paths to ground every claim with immutable source provenance.
            </p>
            <HeroLiveTerminalDesk onEnterConsole={onEnterConsole} />
            <div className="lp-hero-dataset-note" style={{ marginTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
              <span>Deterministic graph traversal &#183; 60-document demo slice &#183; Slack &#183; Linear &#183; GitHub</span>
              <a
                href="https://github.com/toufiqfarhan0/deptrace"
                target="_blank"
                rel="noopener noreferrer"
                className="lp-hero-github-badge"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--c-accent)', fontWeight: 600, textDecoration: 'none', fontSize: 'var(--ts-xs)' }}
              >
                <GitHubIcon size={13} />
                <span>View Code on GitHub &#8599;</span>
              </a>
            </div>
          </div>
          <div className="lp-hero-right" aria-hidden="true">
            <SignalFlowDiagram />
          </div>
        </div>
      </section>

      <JudgeQuickGuideSection onEnterConsole={onEnterConsole} />
      <WorkflowStepsSection />
      <AskVsTraceSection onEnterConsole={onEnterConsole} />
      <TimelineShowcaseSection onEnterConsole={onEnterConsole} />
      <ConflictResolverShowcaseSection onEnterConsole={onEnterConsole} />
      <GraphCanvasShowcaseSection onEnterConsole={onEnterConsole} />
      <SignalsToStateSection />
      <InvestigationExample onEnterConsole={() => onEnterConsole("ask")} />
      <DependencyTracePreview />
      <WhyHydraSection onNavigateToWhyHydra={onNavigateToWhyHydra} />

      <section className="lp-final-cta" aria-labelledby="final-cta-heading">
        <div className="lp-container">
          <div className="lp-final-cta-rule" aria-hidden="true" />
          <h2 className="lp-final-headline" id="final-cta-heading">From fragmented signals to trusted state.</h2>
          <p className="lp-final-sub">Investigate what happened. Trace what changed. Verify why.</p>
          <button className="lp-btn-primary lp-btn-lg" onClick={() => onEnterConsole("ask")} id="lp-final-open-veridex">OPEN VERIDEX</button>
        </div>
      </section>

      {/* 4-Column Minimal Dark Footer (footer.design) */}
      <footer className="lp-footer-4col" role="contentinfo">
        <div className="lp-container">
          <div className="lp-footer-grid">
            <div className="lp-footer-col lp-footer-brand">
              <div className="lp-footer-brand-title">
                <span className="lp-footer-dot" />
                VERIDEX
              </div>
              <p className="lp-footer-tagline">
                Evidence-first dependency intelligence and deterministic knowledge ontology on HydraDB.
              </p>
              <div className="lp-footer-status-badge">
                <span className="lp-footer-status-indicator" />
                <span>HydraDB Cloud v2 Active</span>
              </div>
            </div>

            <div className="lp-footer-col">
              <div className="lp-footer-col-title">Console</div>
              <ul className="lp-footer-list">
                <li><button className="lp-footer-btn" onClick={() => onEnterConsole("ask")}>Grounded Ask</button></li>
                <li><button className="lp-footer-btn" onClick={() => onEnterConsole("trace")}>Trace Graph</button></li>
                <li><button className="lp-footer-btn" onClick={() => onEnterConsole("timeline")}>Incident Timeline</button></li>
                <li><button className="lp-footer-btn" onClick={() => onEnterConsole("conflicts")}>Conflict Arbiter</button></li>
                <li><button className="lp-footer-btn" onClick={() => onEnterConsole("graph")}>Graph Canvas</button></li>
                <li><button className="lp-footer-btn" onClick={() => onEnterConsole("entities")}>Entity Explorer</button></li>
                <li><button className="lp-footer-btn" onClick={() => onEnterConsole("suggestions")}>Query Catalog</button></li>
              </ul>
            </div>

            <div className="lp-footer-col">
              <div className="lp-footer-col-title">Architecture</div>
              <ul className="lp-footer-list">
                <li><button className="lp-footer-btn" onClick={onNavigateToWhyHydra}>Why HydraDB</button></li>
                <li><span className="lp-footer-static">Deterministic BFS</span></li>
                <li><span className="lp-footer-static">Zero Hallucination Gate</span></li>
                <li><span className="lp-footer-static">Provenance Invariants</span></li>
              </ul>
            </div>

            <div className="lp-footer-col">
              <div className="lp-footer-col-title">Repository &amp; Code</div>
              <ul className="lp-footer-list">
                <li>
                  <a
                    href="https://github.com/toufiqfarhan0/deptrace"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="lp-footer-link"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--c-accent)', fontWeight: 600 }}
                  >
                    <GitHubIcon size={12} />
                    <span>GitHub Repository</span>
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com/toufiqfarhan0/deptrace#readme"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="lp-footer-link"
                  >
                    README &amp; Quick Start
                  </a>
                </li>
                <li>
                  <a
                    href="https://github.com/toufiqfarhan0/deptrace/blob/main/LICENSE"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="lp-footer-link"
                  >
                    MIT License
                  </a>
                </li>
                <li><span className="lp-footer-static">100% Provenance Accuracy</span></li>
              </ul>
            </div>
          </div>

          <div className="lp-footer-bottom">
            <div className="lp-footer-copy">
              &copy; 2026 Veridex. Built for Hack Hydra 2026.
            </div>
            <div className="lp-footer-meta">
              <a
                href="https://github.com/toufiqfarhan0/deptrace"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: 'inherit', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4 }}
              >
                <GitHubIcon size={12} />
                <span>github.com/toufiqfarhan0/deptrace</span>
              </a>
              <span>&#183;</span>
              <span>OpenCypher + HydraDB Cloud</span>
              <span>&#183;</span>
              <span>MIT License</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
