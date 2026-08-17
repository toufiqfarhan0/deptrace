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
    id: 'sug-rel-311',
    title: 'What happened with REL-311?',
    category: 'INCIDENTS',
    source: 'SLACK',
    sourceId: 'REL-311',
    entity: 'REL-311',
    description: 'Investigate eu-west latency spikes (p95=4800ms), error rates (1.1%), and support rollback notifications.',
    query: 'What happened with REL-311?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['eu-west', 'rollback', 'tokenizer', 'p95'],
  },
  {
    id: 'sug-model-routing',
    title: 'Why did the team change the model routing?',
    category: 'INCIDENTS',
    source: 'SLACK',
    sourceId: 'strict_model:true',
    entity: 'strict_model:true',
    description: 'Trace model fallbacks, compact-model-v1 degradation, and request-time guard failovers.',
    query: 'Why did the team change the model routing?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['routing', 'strict_model', 'compact-model-v1', 'guard'],
  },
  {
    id: 'sug-kernel-selector-issue',
    title: 'What was the issue with kernel-selector?',
    category: 'INCIDENTS',
    source: 'SLACK',
    sourceId: 'kernel-selector',
    entity: 'kernel-selector',
    description: 'Analyze key normalization issues, soft-evict memory constraints, and fallback routing.',
    query: 'What was the issue with kernel-selector?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['kernel-selector', 'normalization', 'soft-evict'],
  },

  // 2. TECHNICAL ENTITIES & DEPENDENCY TRACING
  {
    id: 'sug-api-search-dep',
    title: 'What is connected to api-search?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'api-search',
    entity: 'api-search',
    description: 'Discover multi-hop dependencies spanning REL-311 and tokenizer version pinning.',
    query: 'What is connected to api-search?',
    type: 'trace',
    badge: 'ENTITY',
    tags: ['api-search', 'REL-311', 'v3.1.1-legacy-tokenizer'],
  },
  {
    id: 'sug-kernel-fallback-policy',
    title: 'What is the kernel-fallback policy?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'kernel-fallback policy',
    entity: 'kernel-fallback policy',
    description: 'Examine runtime fallback guards, quant path handlers, and failover actions.',
    query: 'What is the kernel-fallback policy?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['kernel-fallback', 'quant path', 'guards'],
  },
  {
    id: 'sug-request-time-guard',
    title: 'What actions were taken for request-time guard?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'request-time guard',
    entity: 'request-time guard',
    description: 'Inspect runtime guards enforcing strict model routing and preventing ungrounded inference.',
    query: 'What actions were taken for request-time guard?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['request-time guard', 'strict_model', 'policy'],
  },
  {
    id: 'sug-tokenizer-pin',
    title: 'Trace v3.1.1-legacy-tokenizer dependencies',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'v3.1.1-legacy-tokenizer',
    entity: 'v3.1.1-legacy-tokenizer',
    description: 'Trace 1% canary variant rollout and its connection to incident ticket REL-311.',
    query: 'What is connected to v3.1.1-legacy-tokenizer?',
    type: 'trace',
    badge: 'ENTITY',
    tags: ['tokenizer', 'canary', '1%', 'variant-test'],
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
    title: 'What conversations occurred in #incidents?',
    category: 'SLACK',
    source: 'SLACK',
    sourceId: '#incidents',
    entity: 'REL-311',
    description: 'Slack incident channel discussion covering Pager ACK windows, SLO rewrites, and gateway timeouts.',
    query: 'What conversations occurred in #incidents?',
    type: 'ask',
    badge: 'SLACK',
    tags: ['#incidents', 'SLO', 'pager', 'timeout'],
  },
  {
    id: 'sug-slack-runtime',
    title: 'What discussions occurred in #eng-runtime?',
    category: 'SLACK',
    source: 'SLACK',
    sourceId: '#eng-runtime',
    entity: 'kernel-selector',
    description: 'Runtime engineering discussions regarding tokenizer tail invalidation and VPC cgroup limits.',
    query: 'What discussions occurred in #eng-runtime?',
    type: 'ask',
    badge: 'SLACK',
    tags: ['#eng-runtime', 'tokenizer', 'vpc', 'cgroup'],
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
    { label: 'REL-311 incident', query: 'What happened with REL-311?' },
    { label: 'model routing change', query: 'Why did the team change the model routing?' },
    { label: 'kernel-selector issue', query: 'What was the issue with kernel-selector?' },
    { label: 'strict_model:true', query: 'What is strict_model:true?' },
    { label: 'PR-99501 guardrails', query: 'What is PR-99501 about?' },
  ]
}

/**
 * Shared quick-select entities for Trace console.
 */
export function getQuickTraceEntities() {
  return [
    'REL-311',
    'kernel-selector',
    'api-search',
    'kernel-fallback policy',
    'request-time guard',
    'v3.1.1-legacy-tokenizer',
    'compact-model-v1',
    'strict_model:true',
  ]
}
