import React, { useState, useEffect } from "react"
import ThemeToggle from "./ThemeToggle.jsx"
import { isHydraOnline, getHydraStatusLabel, getHydraAriaLabel } from "../utils/hydraStatus.js"

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
            <div className="lp-source-label">{s.label}</div>
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
  const quickQueries = [
    { label: 'INC-2026', q: 'What happened during incident INC-2026?' },
    { label: 'PR-99501', q: 'What changes were made in PR-99501?' },
    { label: 'REL-311', q: 'What happened with REL-311?' },
    { label: 'kernel-selector', q: 'What is kernel-selector about?' },
  ]

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      onEnterConsole('ask', typedQuery.trim() || 'What happened during incident INC-2026?')
    }
  }

  return (
    <div className="lp-hero-live-desk">
      <div className="lp-terminal-bar">
        <span className="lp-terminal-dot" />
        <span className="lp-terminal-path">veridex://hydradb/enterprise-rag/live</span>
        <span className="lp-terminal-status">HYDRADB READY</span>
      </div>
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
          onClick={() => onEnterConsole('ask', typedQuery.trim() || 'What happened during incident INC-2026?')}
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
            onClick={() => onEnterConsole('ask', item.q)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
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
                  <span className="lp-signal-source-name">{s.label}</span>
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
            <div className="lp-hero-dataset-note" style={{ marginTop: '16px' }}>
              Deterministic graph traversal &#183; 60-document demo slice &#183; Slack &#183; Linear &#183; GitHub
            </div>
          </div>
          <div className="lp-hero-right" aria-hidden="true">
            <SignalFlowDiagram />
          </div>
        </div>
      </section>

      <WorkflowStepsSection />
      <AskVsTraceSection onEnterConsole={onEnterConsole} />
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

      <footer className="lp-footer" role="contentinfo">
        <div className="lp-container">
          <div className="lp-footer-inner">
            <span className="lp-footer-wordmark">VERIDEX</span>
            <span className="lp-footer-sep">&#183;</span>
            <span className="lp-footer-text">Built on HydraDB &#183; EnterpriseRAG-Bench &#183; Hackathon Track 1</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
