import React, { useState, useEffect } from "react"
import ThemeToggle from "./ThemeToggle.jsx"
import { isHydraOnline, getHydraStatusLabel, getHydraAriaLabel } from "../utils/hydraStatus.js"

function SignalFlowDiagram({ onEnterConsole }) {
  const [selectedCard, setSelectedCard] = useState(null)
  const [pulse, setPulse] = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      setPulse((prev) => !prev)
    }, 2500)
    return () => clearInterval(interval)
  }, [])

  const sources = [
    {
      id: "slack",
      brand: "Slack",
      badge: "#proj-payments",
      badgeClass: "slack-badge",
      time: "2m ago",
      icon: "💬",
      excerpt: 'Sarah: "We agreed on Postgres optimistic locking for transaction retries..."',
    },
    {
      id: "github",
      brand: "GitHub",
      badge: "PR #1402",
      badgeClass: "github-badge",
      time: "18m ago",
      icon: "🐙",
      excerpt: "Commit 8f3a92: Updated DB config & timeout threshold to 300ms...",
    },
    {
      id: "jira",
      brand: "Jira",
      badge: "PAY-892",
      badgeClass: "jira-badge",
      time: "1h ago",
      icon: "🔷",
      excerpt: 'Ticket PAY-892 marked In Progress: "Deprecate v1 auth tokens..."',
    },
    {
      id: "linear",
      brand: "Linear",
      badge: "ENG-341",
      badgeClass: "linear-badge",
      time: "3h ago",
      icon: "📐",
      excerpt: 'Issue ENG-341 updated: "Migration plan for distributed lock timeouts..."',
    },
    {
      id: "confluence",
      brand: "Confluence",
      badge: "Tech Spec v2.4",
      badgeClass: "confluence-badge",
      time: "Yesterday",
      icon: "📄",
      excerpt: 'Page updated: "Architecture RFC 104: Event-sourced ledger auth..."',
    },
  ]

  const featurePills = [
    { id: "identity", icon: "⚡", label: "Identity Resolution" },
    { id: "temporal", icon: "⏱️", label: "Temporal Reasoning" },
    { id: "conflict", icon: "💧", label: "Conflict Detection" },
    { id: "provenance", icon: "🔗", label: "Evidence & Provenance" },
  ]

  return (
    <div className="deptrace-hero-diagram-container">
      {/* 3-Column Diagram Layout */}
      <div className="deptrace-diagram-grid">
        
        {/* LEFT COLUMN: Input Source Stack */}
        <div className="deptrace-source-col">
          {sources.map((s) => {
            const isSelected = selectedCard === s.id
            return (
              <div
                key={s.id}
                className={`deptrace-source-card ${isSelected ? "selected" : ""}`}
                onClick={() => setSelectedCard(isSelected ? null : s.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    setSelectedCard(isSelected ? null : s.id)
                  }
                }}
              >
                <div className="deptrace-source-top">
                  <div className="deptrace-source-brand">
                    <span className="deptrace-brand-icon">{s.icon}</span>
                    <span className="deptrace-brand-name">{s.brand}</span>
                    <span className={`deptrace-tag ${s.badgeClass}`}>{s.badge}</span>
                  </div>
                  <span className="deptrace-source-time">{s.time}</span>
                </div>
                <div className="deptrace-source-excerpt">{s.excerpt}</div>
              </div>
            )
          })}
        </div>

        {/* CONNECTOR 1: Left SVG Dotted Flow */}
        <div className="deptrace-flow-connector left-flow" aria-hidden="true">
          <svg viewBox="0 0 100 400" preserveAspectRatio="none" className="flow-svg">
            <path d="M0 40 Q50 40 100 200" className={`flow-path ${pulse ? "pulse-1" : ""}`} />
            <path d="M0 120 Q50 120 100 200" className={`flow-path ${pulse ? "pulse-2" : ""}`} />
            <path d="M0 200 Q50 200 100 200" className={`flow-path ${pulse ? "pulse-3" : ""}`} />
            <path d="M0 280 Q50 280 100 200" className={`flow-path ${pulse ? "pulse-4" : ""}`} />
            <path d="M0 360 Q50 360 100 200" className={`flow-path ${pulse ? "pulse-5" : ""}`} />
          </svg>
        </div>

        {/* CENTER COLUMN: DepTrace Core Node & Feature Pills */}
        <div className="deptrace-center-col">
          {/* Main Logo Card */}
          <div className="deptrace-logo-card">
            <div className="deptrace-logo-glow" />
            <div className="deptrace-logo-icon">
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="10" r="4" fill="#a855f7" />
                <circle cx="10" cy="28" r="4" fill="#8b5cf6" />
                <circle cx="30" cy="28" r="4" fill="#06b6d4" />
                <path d="M20 10 L10 28 M20 10 L30 28 M10 28 L30 28" stroke="rgba(168,85,247,0.7)" strokeWidth="2" strokeDasharray="3 3" />
              </svg>
            </div>
            <div className="deptrace-logo-title">DepTrace</div>
          </div>

          {/* Feature Pills Stack */}
          <div className="deptrace-feature-pills">
            {featurePills.map((p) => (
              <div key={p.id} className="deptrace-feature-pill">
                <span className="pill-icon">{p.icon}</span>
                <span className="pill-label">{p.label}</span>
                <span className="pill-dot" />
              </div>
            ))}
          </div>

          {/* Synthesizing Action CTA */}
          <div className="deptrace-synth-wrapper">
            <button
              className="deptrace-synth-btn"
              onClick={() => onEnterConsole("ask")}
              type="button"
              id="deptrace-synth-action"
            >
              <span>SYNTHESIZING</span>
              <span className="synth-arrow">→</span>
            </button>
          </div>
        </div>

        {/* CONNECTOR 2: Right SVG Flow */}
        <div className="deptrace-flow-connector right-flow" aria-hidden="true">
          <svg viewBox="0 0 100 400" preserveAspectRatio="none" className="flow-svg">
            <path d="M0 200 Q50 200 100 200" className="flow-path right-path" />
          </svg>
        </div>

        {/* RIGHT COLUMN: Reconstructed Output Card */}
        <div className="deptrace-output-col">
          <div className="deptrace-resolution-card">
            {/* Header */}
            <div className="resolution-card-header">
              <div className="resolution-header-left">
                <div className="dt-badge">DT</div>
                <div className="resolution-title">Dependency Resolution</div>
              </div>
              <div className="resolution-header-right">
                <span className="status-badge-resolved">RESOLVED</span>
              </div>
            </div>
            <div className="graph-node-ref">Graph Node #892-C</div>

            {/* Block 1: Root Cause */}
            <div className="resolution-block root-cause-block">
              <div className="block-label">ROOT CAUSE</div>
              <div className="block-text">
                Uncoordinated DB connection timeout overrides between Slack thread decision & PR #1402 default configuration.
              </div>
            </div>

            {/* Block 2: Linked Decision */}
            <div className="resolution-block linked-decision-block">
              <div className="block-label">LINKED DECISION</div>
              <div className="linked-decision-row">
                <span className="decision-title">RFC-104: Optimistic Locking & Audit Trail</span>
                <span className="confirmed-pill">CONFIRMED</span>
              </div>
            </div>

            {/* Block 3: Why */}
            <div className="resolution-block why-block">
              <div className="block-label">WHY</div>
              <div className="why-text">
                Slack agreement in <strong>#proj-payments</strong> overrode Jira <strong>PAY-892</strong> default lock timeouts without updating the active GitHub PR <strong>#1402</strong> env variables.
              </div>
            </div>

            {/* Block 4: Connected Provenance */}
            <div className="resolution-block provenance-block">
              <div className="block-label">CONNECTED EVIDENCE PROVENANCE</div>
              <div className="provenance-icons-row">
                <span className="prov-icon" title="Slack">💬</span>
                <span className="prov-icon" title="GitHub">🐙</span>
                <span className="prov-icon" title="Jira">🔷</span>
                <span className="prov-icon" title="Linear">📐</span>
                <span className="prov-icon" title="Confluence">📄</span>
                <span className="prov-count">5 verified sources</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Bottom Tagline Banner */}
      <div className="deptrace-bottom-banner">
        <span className="banner-sparkle">✦</span>
        <span className="banner-text">From scattered threads to a traceable dependency graph.</span>
      </div>
    </div>
  )
}

function WorkflowStepsSection({ onEnterConsole }) {
  const steps = [
    {
      step: "01",
      title: "ASK",
      headline: "Ask a question about your engineering knowledge.",
      desc: "Query incidents, pull requests, Linear issues, and Slack conversations in natural language without complex query syntax.",
    },
    {
      step: "02",
      title: "CONNECT",
      headline: "DepTrace resolves relationships across HydraDB.",
      desc: "HydraDB traverses cross-system entity relationships and extracts bounded facts with strict message and document IDs.",
    },
    {
      step: "03",
      title: "VERIFY",
      headline: "Review the evidence, provenance, and dependency paths.",
      desc: "Gemini synthesizes a clear answer citing exact evidence items [E1, E2]. Trace dependencies to verify root causes.",
    },
  ]

  return (
    <section className="lp-section" aria-labelledby="workflow-heading">
      <div className="lp-container">
        <div className="lp-section-eyebrow" id="workflow-heading">HOW IT WORKS</div>
        <h2 className="lp-section-title">From fragmented signals to grounded investigation.</h2>
        <p className="lp-section-body">
          A predictable 3-step investigation pipeline designed for engineering teams and postmortem investigations.
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
          Whether you need a direct evidence-backed answer to an incident question or want to map multi-hop component dependencies, DepTrace provides dedicated workflows.
        </p>

        <div className="lp-comparison-grid">
          {/* ASK CARD */}
          <div className="lp-comparison-card">
            <div className="lp-comparison-header">
              <div className="lp-comparison-badge ask">ASK MODE</div>
              <h3 className="lp-comparison-title">Get an evidence-backed answer.</h3>
            </div>
            <p className="lp-comparison-desc">
              Ask natural language questions about incidents, tickets, PRs, and team decisions. DepTrace returns a grounded answer strictly citing retrieved graph evidence.
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

function WhyHydraSection({ onNavigateToWhyHydra }) {
  const steps = [
    { label: "Raw Enterprise Signals", desc: "Slack, Linear, GitHub, Confluence, Jira" },
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
        <p className="lp-section-body">Traditional RAG architectures approximate retrieval with vector similarity. DepTrace uses HydraDB's graph-aware retrieval layer to resolve relationships and provenance before synthesis begins.</p>
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
          <button className="lp-btn-ghost" onClick={onNavigateToWhyHydra} id="lp-explore-arch-btn">HOW DEPTRACE WORKS &#8594;</button>
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
      <header className={`lp-nav${scrolled ? " lp-nav--scrolled" : ""}`} role="banner">
        <div className="lp-nav-inner">
          <div className="lp-nav-wordmark">
            <span className="lp-nav-logo">DEPTRACE</span>
            <span className="lp-nav-tag">BETA</span>
          </div>
          <nav className="lp-nav-links" aria-label="Product navigation">
            <button className="lp-nav-link" onClick={() => onEnterConsole("ask")} id="lp-nav-investigate">ASK</button>
            <button className="lp-nav-link" onClick={() => onEnterConsole("trace")} id="lp-nav-trace">TRACE</button>
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
            <button className="lp-btn-primary lp-btn-sm" onClick={() => onEnterConsole("ask")} id="lp-nav-open-console">OPEN CONSOLE</button>
          </div>
        </div>
      </header>

      {/* HERO SECTION MATCHING REFERENCE MOCKUP GRAPHIC */}
      <section className="lp-hero" aria-labelledby="hero-heading">
        <div className="lp-hero-inner">
          {/* Two-Column Top Headline Row */}
          <div className="deptrace-hero-header-row">
            <div className="deptrace-hero-col-left">
              <h1 className="deptrace-main-headline" id="hero-heading">
                Your engineering truth is <span className="purple-gradient-text">scattered.</span>
              </h1>
              <p className="deptrace-main-sub">
                Disjointed discussions, tickets, specs, and PRs mask crucial architecture context.
              </p>
            </div>
            <div className="deptrace-hero-col-right">
              <h2 className="deptrace-main-headline">
                DepTrace reconstructs what your team <span className="purple-gradient-text">actually decided.</span>
              </h2>
              <p className="deptrace-main-sub">
                Automated dependency mapping with cryptographic evidence & provenance graph.
              </p>
            </div>
          </div>

          {/* Hero Visual Flow Diagram */}
          <SignalFlowDiagram onEnterConsole={onEnterConsole} />
        </div>
      </section>

      <WorkflowStepsSection onEnterConsole={onEnterConsole} />
      <AskVsTraceSection onEnterConsole={onEnterConsole} />
      <WhyHydraSection onNavigateToWhyHydra={onNavigateToWhyHydra} />

      <section className="lp-final-cta" aria-labelledby="final-cta-heading">
        <div className="lp-container">
          <div className="lp-final-cta-rule" aria-hidden="true" />
          <h2 className="lp-final-headline" id="final-cta-heading">From fragmented signals to trusted state.</h2>
          <p className="lp-final-sub">Investigate what happened. Trace what changed. Verify why.</p>
          <button className="lp-btn-primary lp-btn-lg" onClick={() => onEnterConsole("ask")} id="lp-final-open-veridex">OPEN DEPTRACE</button>
        </div>
      </section>

      <footer className="lp-footer" role="contentinfo">
        <div className="lp-container">
          <div className="lp-footer-inner">
            <span className="lp-footer-wordmark">DEPTRACE</span>
            <span className="lp-footer-sep">&#183;</span>
            <span className="lp-footer-text">Built on HydraDB &#183; Enterprise Knowledge Graph</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
