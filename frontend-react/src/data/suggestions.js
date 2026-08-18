/**
 * Shared Deterministic Suggestion Catalog for Veridex (Local HydraDB).
 *
 * Derived exclusively from verified Local HydraDB entities, indexed records,
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
    title: 'What happened with support ticket REL-311?',
    category: 'INCIDENTS',
    source: 'SLACK',
    sourceId: 'REL-311',
    entity: 'REL-311',
    description: 'Investigate release notes, error rates in eu-west, and the v3.1.1 legacy tokenizer variant test in api-search.',
    query: 'What happened with REL-311?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['REL-311', 'tokenizer', 'eu-west', 'api-search'],
  },
  {
    id: 'sug-kernel-selector',
    title: 'What was the issue with kernel-selector?',
    category: 'INCIDENTS',
    source: 'GRAPH',
    sourceId: 'kernel-selector',
    entity: 'kernel-selector',
    description: 'Examine latency regression mitigation, soft-evict configuration, and key normalization policies.',
    query: 'What was the issue with kernel-selector?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['kernel-selector', 'soft-evict', 'revert', 'latency'],
  },
  {
    id: 'sug-inf-4921',
    title: 'What is INF-4921 about?',
    category: 'INCIDENTS',
    source: 'LINEAR',
    sourceId: 'INF-4921',
    entity: 'INF-4921',
    description: 'Track ticket INF-4921 for oncall reader access grants and postmortem follow-up actions.',
    query: 'What is INF-4921 about?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['INF-4921', 'oncall-readers', 'access-grant', 'security'],
  },
  {
    id: 'sug-legacy-tokenizer',
    title: 'What happened during the legacy tokenizer test?',
    category: 'INCIDENTS',
    source: 'SLACK',
    sourceId: 'v3.1.1-legacy-tokenizer',
    entity: 'v3.1.1-legacy-tokenizer',
    description: 'Trace the 1% targeted variant test of v3.1.1-legacy-tokenizer during api-search latency evaluation.',
    query: 'What happened during the legacy tokenizer test?',
    type: 'ask',
    badge: 'INCIDENT',
    tags: ['v3.1.1-legacy-tokenizer', 'api-search', 'variant-test'],
  },

  // 2. TECHNICAL ENTITIES & DEPENDENCY TRACING
  {
    id: 'sug-strict-model',
    title: 'What is strict_model:true?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'strict_model:true',
    entity: 'strict_model:true',
    description: 'Examine unreleased request-time model parameter recommendation and fallback routing diagnostics.',
    query: 'What is strict_model:true?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['strict_model:true', 'routing', 'fallback', 'config'],
  },
  {
    id: 'sug-api-search',
    title: 'What happened with api-search routing?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'api-search',
    entity: 'api-search',
    description: 'Trace api-search dependencies to REL-311 and legacy tokenizer rollout variants.',
    query: 'What happened with api-search?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['api-search', 'REL-311', 'tokenizer', 'routing'],
  },
  {
    id: 'sug-compact-model',
    title: 'Why was compact-model-v1 deployed?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'compact-model-v1',
    entity: 'compact-model-v1',
    description: 'Analyze fallback routing snippets and prototype rule definitions for compact-model-v1.',
    query: 'Why was compact-model-v1 deployed?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['compact-model-v1', 'routing', 'fallback'],
  },
  {
    id: 'sug-primary-v2',
    title: 'What is primary-v2 model routing?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'primary-v2',
    entity: 'primary-v2',
    description: 'Inspect primary-v2 model configuration and token threshold fallback rules.',
    query: 'What is primary-v2?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['primary-v2', 'fallback-rule', 'model'],
  },
  {
    id: 'sug-request-guard',
    title: 'What is the request-time guard canary?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'request-time guard',
    entity: 'request-time guard',
    description: 'Trace ETA and rollout verification for the request-time guard canary across services.',
    query: 'What is the request-time guard canary?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['request-time guard', 'canary', 'rollout'],
  },
  {
    id: 'sug-soft-evict',
    title: 'What is soft-evict config?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'soft-evict config',
    entity: 'soft-evict config',
    description: 'Review memory compaction triggers and soft-evict cache configuration directives.',
    query: 'What is soft-evict config?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['soft-evict', 'cache', 'memory', 'config'],
  },
  {
    id: 'sug-key-norm',
    title: 'What is enable key normalization?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'enable key normalization',
    entity: 'enable key normalization',
    description: 'Inspect trace key normalization actions and cache hit-rate dashboard monitoring.',
    query: 'What is enable key normalization?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['normalization', 'trace_key', 'cache'],
  },
  {
    id: 'sug-fallback-policy',
    title: 'Why does fallback routing occur?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'kernel-fallback policy',
    entity: 'kernel-fallback policy',
    description: 'Trace postmortem actions and performance test requirements for kernel fallback policies.',
    query: 'Why does fallback routing occur?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['fallback', 'kernel-fallback policy', 'routing'],
  },
  {
    id: 'sug-quant-path',
    title: 'What is the quant path fallback?',
    category: 'ENTITIES',
    source: 'GRAPH',
    sourceId: 'quant path',
    entity: 'quant path',
    description: 'Inspect quantization fallback execution paths and regression prevention steps.',
    query: 'What is the quant path fallback?',
    type: 'ask',
    badge: 'ENTITY',
    tags: ['quant path', 'quantization', 'fallback'],
  },

  // 3. SYSTEM & OPERATIONS
  {
    id: 'sug-grafana',
    title: 'What dashboards were set up in Grafana?',
    category: 'OPERATIONS',
    source: 'GRAPH',
    sourceId: 'Grafana',
    entity: 'Grafana',
    description: 'Review Grafana error queries, sample payloads, hit-rate, and fragmentation dashboards.',
    query: 'What dashboards were set up in Grafana?',
    type: 'ask',
    badge: 'OPERATIONS',
    tags: ['Grafana', 'dashboards', 'monitoring', 'metrics'],
  },
  {
    id: 'sug-deploy-job',
    title: 'What happened with DeployJob #445?',
    category: 'OPERATIONS',
    source: 'GITHUB',
    sourceId: 'DeployJob #445',
    entity: 'DeployJob #445',
    description: 'Investigate CI pipeline failure on embed screenshot step for DeployJob #445.',
    query: 'What happened with DeployJob #445?',
    type: 'ask',
    badge: 'OPERATIONS',
    tags: ['DeployJob #445', 'CI', 'render-timeout'],
  },
  {
    id: 'sug-node-sdk',
    title: 'What was updated in the Node SDK?',
    category: 'OPERATIONS',
    source: 'GITHUB',
    sourceId: 'Node SDK',
    entity: 'Node SDK',
    description: 'Examine Node SDK updates, metrics API dependencies, and screenshot rendering changes.',
    query: 'What was updated in the Node SDK?',
    type: 'ask',
    badge: 'OPERATIONS',
    tags: ['Node SDK', 'metrics API', 'updates'],
  },
  {
    id: 'sug-access-grant',
    title: 'What is access grant to group:oncall-readers?',
    category: 'OPERATIONS',
    source: 'LINEAR',
    sourceId: 'access grant to group:oncall-readers',
    entity: 'access grant to group:oncall-readers',
    description: 'Trace temporary oncall reader role assignments and expiration timestamps.',
    query: 'What is access grant to group:oncall-readers?',
    type: 'ask',
    badge: 'OPERATIONS',
    tags: ['access-grant', 'oncall-readers', 'security', 'role'],
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
    { label: 'kernel-selector issue', query: 'What was the issue with kernel-selector?' },
    { label: 'strict_model:true', query: 'What is strict_model:true?' },
    { label: 'api-search latency', query: 'What happened with api-search?' },
    { label: 'INF-4921 ticket', query: 'What is INF-4921 about?' },
  ]
}

/**
 * Shared quick-select entities for Trace console.
 */
export function getQuickTraceEntities() {
  return [
    'REL-311',
    'kernel-selector',
    'strict_model:true',
    'api-search',
    'v3.1.1-legacy-tokenizer',
    'compact-model-v1',
    'INF-4921',
    'Grafana',
  ]
}
