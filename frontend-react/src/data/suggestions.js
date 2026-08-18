/**
 * Shared Deterministic Suggestion Catalog for Veridex.
 *
 * Derived exclusively from verified HydraDB entities, indexed records,
 * and multi-source dataset slices (Slack, Linear, GitHub).
 *
 * FROZEN DATASET BOUNDARY: 60 Documents (20 Slack, 20 Linear, 20 GitHub)
 */

export const DATASET_STATS = {
  total: 60,
  slack: 20,
  linear: 20,
  github: 20,
  isFrozen: true,
}

export const SUGGESTIONS_CATALOG = [
  // 1. INCIDENTS & CRITICAL ALERTS
  {
    id: 'sug-inc-2026',
    title: 'What happened during incident INC-2026?',
    category: 'INCIDENTS',
    source: 'SLACK',
    sourceId: 'INC-2026',
    entity: 'INC-2026',
    description: 'Investigate cluster error rate spikes, KMS decrypt anomalies, and frontend-proxy connection timeouts across #incidents and #eng-security.',
    query: 'What happened during incident INC-2026?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['INC-2026', 'latency', 'KMS', '#incidents'],
  },
  {
    id: 'sug-bluecrest-surges',
    title: 'What caused the Bluecrest gateway timeouts?',
    category: 'INCIDENTS',
    source: 'SLACK',
    sourceId: '2139001234',
    entity: 'Bluecrest',
    description: 'Analyze elevated 504 and 408 gateway timeouts and WebSocket disconnects observed for tenant Bluecrest (bch-82).',
    query: 'What caused the Bluecrest gateway timeouts?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['Bluecrest', 'bch-82', '504', 'gateway'],
  },
  {
    id: 'sug-tokenizer-evict-latency',
    title: 'What caused the tokenizer eviction latency jump in #eng-runtime?',
    category: 'INCIDENTS',
    source: 'SLACK',
    sourceId: '1895001234',
    entity: 'v7.0 rollout',
    description: 'Trace p95 and p99 tail latency degradation (2.5-3x) following the v7.0 tokenizer eviction rollout in #eng-runtime.',
    query: 'What caused the tokenizer eviction latency jump after the v7.0 rollout?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['#eng-runtime', 'v7.0', 'p95', 'latency'],
  },

  // 2. TECHNICAL ENTITIES & DEPENDENCY TRACING
  {
    id: 'sug-kms-guardrails',
    title: 'What are the KMS guardrails in PR-99501?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'PR-99501',
    entity: 'PR-99501',
    description: 'Examine service-scoped KMS guardrails, audit ingestion harmonizer, and credential protection policies.',
    query: 'What are the KMS guardrails in PR-99501?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['KMS', 'guardrails', 'PR-99501', 'security'],
  },
  {
    id: 'sug-overload-signal-fusion',
    title: 'What is the overload signal fusion policy in ENG-68910?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'ENG-68910',
    entity: 'ENG-68910',
    description: 'Inspect overload signal fusion and protective tripping rules deployed to safeguard fleet availability.',
    query: 'What is the overload signal fusion policy in ENG-68910?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['overload', 'ENG-68910', 'protection', 'fusion'],
  },
  {
    id: 'sug-interop-fallback-tools',
    title: 'What is the interop fallback policy in ENG-30521?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'ENG-30521',
    entity: 'ENG-30521',
    description: 'Trace interop-fallback policies for tool calls with naming mappers and distributed telemetry boundaries.',
    query: 'What is the interop fallback policy for tool calls in ENG-30521?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['interop', 'tools', 'ENG-30521', 'telemetry'],
  },
  {
    id: 'sug-deferred-indexing-rag',
    title: 'What is the deferred-indexing playbook in PR-209876?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'PR-209876',
    entity: 'PR-209876',
    description: 'Examine deferred-indexing RAG playbooks and streaming tool-proxy adapters for enterprise retrieval.',
    query: 'What is the deferred-indexing playbook in PR-209876?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['RAG', 'deferred-indexing', 'PR-209876', 'playbook'],
  },

  // 3. LINEAR ISSUES
  {
    id: 'sug-eng-30521',
    title: 'What is ENG-30521 about?',
    category: 'LINEAR',
    source: 'LINEAR',
    sourceId: 'ENG-30521',
    entity: 'ENG-30521',
    description: 'Linear issue detailing interop-fallback policies and tool-execution boundary conditions.',
    query: 'What is ENG-30521 about?',
    type: 'ask',
    badge: 'LINEAR',
    tags: ['interop', 'fallback-policy', 'tools'],
  },
  {
    id: 'sug-eng-68910',
    title: 'What is ENG-68910 about?',
    category: 'LINEAR',
    source: 'LINEAR',
    sourceId: 'ENG-68910',
    entity: 'ENG-68910',
    description: 'Linear engineering ticket covering overload signal fusion and fleet protection guards.',
    query: 'What is ENG-68910 about?',
    type: 'ask',
    badge: 'LINEAR',
    tags: ['overload', 'signal-fusion', 'protection'],
  },
  {
    id: 'sug-eng-233901',
    title: 'What is ENG-233901 about?',
    category: 'LINEAR',
    source: 'LINEAR',
    sourceId: 'ENG-233901',
    entity: 'ENG-233901',
    description: 'KMS chaos failover harness, crypto key rotation, and credential failover validations.',
    query: 'What is ENG-233901 about?',
    type: 'ask',
    badge: 'LINEAR',
    tags: ['KMS', 'failover', 'chaos', 'security'],
  },
  {
    id: 'sug-des-23981',
    title: 'What is DES-23981 about?',
    category: 'LINEAR',
    source: 'LINEAR',
    sourceId: 'DES-23981',
    entity: 'DES-23981',
    description: 'Tenant dependency graph specification and deferred-execution data architecture.',
    query: 'What is DES-23981 about?',
    type: 'ask',
    badge: 'LINEAR',
    tags: ['tenant', 'dependency-graph', 'architecture'],
  },

  // 4. GITHUB PULL REQUESTS
  {
    id: 'sug-pr-99501',
    title: 'What is PR-99501 about?',
    category: 'GITHUB',
    source: 'GITHUB',
    sourceId: 'PR-99501',
    entity: 'PR-99501',
    description: 'GitHub pull request adding service-scoped KMS guardrails and retry handling policies.',
    query: 'What is PR-99501 about?',
    type: 'ask',
    badge: 'GITHUB',
    tags: ['KMS', 'guardrails', 'retry', 'security'],
  },
  {
    id: 'sug-pr-482199',
    title: 'What is PR-482199 about?',
    category: 'GITHUB',
    source: 'GITHUB',
    sourceId: 'PR-482199',
    entity: 'PR-482199',
    description: 'Pull request normalizing function-invoke headers and distributed retry logic.',
    query: 'What is PR-482199 about?',
    type: 'ask',
    badge: 'GITHUB',
    tags: ['headers', 'invocation', 'retry'],
  },
  {
    id: 'sug-pr-209876',
    title: 'What is PR-209876 about?',
    category: 'GITHUB',
    source: 'GITHUB',
    sourceId: 'PR-209876',
    entity: 'PR-209876',
    description: 'Pull request establishing deferred-indexing playbooks for enterprise knowledge retrieval.',
    query: 'What is PR-209876 about?',
    type: 'ask',
    badge: 'GITHUB',
    tags: ['RAG', 'deferred-indexing', 'playbook'],
  },

  // 5. SLACK CONVERSATIONS & CHANNELS
  {
    id: 'sug-slack-incidents',
    title: 'What discussions occurred in #incidents regarding incident INC-2026?',
    category: 'SLACK',
    source: 'SLACK',
    sourceId: 'INC-2026',
    entity: 'INC-2026',
    description: 'Slack incident channel discussion covering Pager ACK windows, SLO rewrites, and gateway timeouts for incident INC-2026.',
    query: 'What discussions occurred in #incidents regarding incident INC-2026?',
    type: 'ask',
    badge: 'SLACK',
    tags: ['#incidents', 'INC-2026', 'SLO', 'pager'],
  },
  {
    id: 'sug-slack-runtime',
    title: 'What discussions occurred in #eng-runtime regarding VPC disk cgroup limits?',
    category: 'SLACK',
    source: 'SLACK',
    sourceId: '2076549999',
    entity: '2076549999',
    description: 'Runtime engineering discussions regarding VPC disk cgroup limits and container smoke tests in #eng-runtime.',
    query: 'What discussions occurred in #eng-runtime regarding VPC disk cgroup limits?',
    type: 'ask',
    badge: 'SLACK',
    tags: ['#eng-runtime', 'vpc', 'cgroup', 'disk'],
  },

  // 6. CROSS-SOURCE REASONING
  {
    id: 'sug-cross-source-kms',
    title: 'Trace KMS dependencies across GitHub and Linear',
    category: 'CROSS-SOURCE',
    source: 'GRAPH',
    sourceId: 'PR-99501',
    entity: 'PR-99501',
    description: 'Correlate PR-99501 code guardrails with Linear issue ENG-233901 KMS chaos testing.',
    query: 'What is connected to PR-99501?',
    type: 'trace',
    badge: 'CROSS-SOURCE',
    tags: ['KMS', 'cross-source', 'PR-99501', 'ENG-233901'],
  },
]

/**
 * Filter suggestions by category and search term.
 */
export function getFilteredSuggestions(category = 'ALL', search = '') {
  const normSearch = search.trim().toLowerCase()
  return SUGGESTIONS_CATALOG.filter((item) => {
    // Category match
    const catMatch =
      category === 'ALL' ||
      item.category === category ||
      item.source === category

    if (!catMatch) return false
    if (!normSearch) return true

    // Text search matching
    return (
      item.title.toLowerCase().includes(normSearch) ||
      item.entity.toLowerCase().includes(normSearch) ||
      item.sourceId.toLowerCase().includes(normSearch) ||
      item.description.toLowerCase().includes(normSearch) ||
      item.category.toLowerCase().includes(normSearch) ||
      item.source.toLowerCase().includes(normSearch) ||
      item.tags.some((t) => t.toLowerCase().includes(normSearch))
    )
  })
}

/**
 * Shared suggested inquiry queries for Ask console.
 */
export function getInquiryQueries() {
  return [
    { label: 'INC-2026 incident', query: 'What happened during incident INC-2026?' },
    { label: 'PR-99501 guardrails', query: 'What is PR-99501 about?' },
    { label: 'ENG-68910 overload fusion', query: 'What is ENG-68910 about?' },
    { label: 'ENG-233901 KMS chaos', query: 'What is ENG-233901 about?' },
    { label: 'Bluecrest timeouts', query: 'What caused the Bluecrest gateway timeouts?' },
  ]
}

/**
 * Shared quick-select entities for Trace console.
 */
export function getQuickTraceEntities() {
  return [
    'PR-99501',
    'INC-2026',
    'ENG-68910',
    'ENG-233901',
    'ENG-30521',
    'DES-23981',
    'PR-482199',
    'PR-209876',
  ]
}
