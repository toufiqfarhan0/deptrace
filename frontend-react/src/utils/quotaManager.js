/**
 * Progressive User Quota and Rate Limit Manager for Veridex.
 * 
 * Provides a smart progressive demo quota system:
 * - Base tier: 3 queries allowed.
 * - 1st Refresh bonus: Grants +2 queries (5 total).
 * - 2nd Refresh bonus: Grants +1 query (6 total).
 * - Max reached: Professional notice that 6 queries is plenty to evaluate the project.
 */

import { useState, useEffect, useCallback } from 'react'

export const BASE_QUOTA = 3
export const REFRESH_1_BONUS = 2
export const REFRESH_2_BONUS = 1
export const MAX_ALLOWED_TOTAL = 6

export const STORAGE_KEY = 'veridex_user_quota_count'
export const STORAGE_KEY_USED = 'veridex_user_quota_count'
export const STORAGE_KEY_STAGE = 'veridex_quota_refresh_stage'

export const RATE_LIMIT_MESSAGE = 'This model reached limit'

export const QUOTA_MESSAGES = {
  STAGE_0_LIMIT: "Initial demo quota reached (3/3 queries used). Refresh the page to unlock 2 additional review queries!",
  STAGE_1_LIMIT: "Bonus quota reached (5/5 queries used). Refresh the page one more time for 1 final test query!",
  STAGE_2_LIMIT: "Demo evaluation completed (6/6 queries tested). That's plenty of evidence to evaluate Veridex! Explore the pre-computed graph & benchmarks or clone the repository to run locally.",
  STAGE_3_LIMIT: "Evaluation quota completed (6/6 queries tested). You've thoroughly explored all core features! Check the Why HydraDB tab for full benchmark telemetry or run locally with your own API keys.",
}

// Backward-compatible alias
export const QUOTA_STUDENT_MESSAGE = QUOTA_MESSAGES.STAGE_0_LIMIT

const EVENT_NAME = 'veridex:quota-changed'

/**
 * Get total queries used from localStorage.
 */
export function getQuotaUsed() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_USED)
    if (raw !== null) {
      const parsed = parseInt(raw, 10)
      return isNaN(parsed) || parsed < 0 ? 0 : parsed
    }
  } catch {
    // Ignore localStorage access failures in SSR or restricted iframe
  }
  return 0
}

/**
 * Get the current refresh stage (0, 1, 2, 3).
 */
export function getRefreshStage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_STAGE)
    if (raw !== null) {
      const parsed = parseInt(raw, 10)
      return isNaN(parsed) || parsed < 0 ? 0 : Math.min(parsed, 3)
    }
  } catch {
    // Ignore
  }
  return 0
}

/**
 * Get maximum allowed quota for a given stage.
 */
export function getMaxQuotaForStage(stage) {
  if (stage === 0) return BASE_QUOTA // 3
  if (stage === 1) return BASE_QUOTA + REFRESH_1_BONUS // 5
  return MAX_ALLOWED_TOTAL // 6
}

/**
 * Get the current maximum quota based on current stage.
 */
export function getMaxQuota() {
  const stage = getRefreshStage()
  return getMaxQuotaForStage(stage)
}

/**
 * Get remaining actions/queries in current stage.
 */
export function getRemainingQuota() {
  const used = getQuotaUsed()
  const max = getMaxQuota()
  return Math.max(0, max - used)
}

/**
 * Check if the user has exceeded quota for their current stage.
 */
export function isQuotaExceeded() {
  return getRemainingQuota() <= 0
}

/**
 * Get the appropriate message based on current stage and usage.
 */
export function getQuotaMessage() {
  const stage = getRefreshStage()
  if (stage === 0) {
    return QUOTA_MESSAGES.STAGE_0_LIMIT
  } else if (stage === 1) {
    return QUOTA_MESSAGES.STAGE_1_LIMIT
  } else if (stage === 2) {
    return QUOTA_MESSAGES.STAGE_2_LIMIT
  }
  return QUOTA_MESSAGES.STAGE_3_LIMIT
}

/**
 * Initialize / Grant refresh bonuses on page load.
 * Advances stage if the previous stage's limit was reached.
 */
export function initRefreshBonus() {
  try {
    if (typeof window === 'undefined') return

    const used = getQuotaUsed()
    let stage = getRefreshStage()

    // Check if eligible for stage upgrades upon reload
    if (used >= BASE_QUOTA && stage === 0) {
      stage = 1
      localStorage.setItem(STORAGE_KEY_STAGE, '1')
    } else if (used >= (BASE_QUOTA + REFRESH_1_BONUS) && stage === 1) {
      stage = 2
      localStorage.setItem(STORAGE_KEY_STAGE, '2')
    } else if (used >= MAX_ALLOWED_TOTAL && stage === 2) {
      stage = 3
      localStorage.setItem(STORAGE_KEY_STAGE, '3')
    }
  } catch {
    // Ignore storage errors
  }
}

// Auto-run on module load in browser
if (typeof window !== 'undefined') {
  initRefreshBonus()
}

/**
 * Dispatch an event to synchronize all listeners/components across tabs or in-page.
 */
function notifyQuotaChange() {
  if (typeof window !== 'undefined' && window.dispatchEvent) {
    try {
      window.dispatchEvent(new CustomEvent(EVENT_NAME, {
        detail: {
          used: getQuotaUsed(),
          remaining: getRemainingQuota(),
          stage: getRefreshStage(),
        }
      }))
    } catch {
      // Ignore event dispatch errors
    }
  }
}

/**
 * Attempt to consume 1 quota unit.
 */
export function consumeQuota() {
  const current = getQuotaUsed()
  const max = getMaxQuota()
  const msg = getQuotaMessage()

  if (current >= max) {
    notifyQuotaChange()
    return {
      allowed: false,
      remaining: 0,
      message: msg,
    }
  }

  const next = current + 1
  try {
    localStorage.setItem(STORAGE_KEY_USED, String(next))
  } catch {
    // Ignore
  }

  notifyQuotaChange()
  return {
    allowed: true,
    remaining: Math.max(0, max - next),
  }
}

/**
 * Reset quota (useful for testing or developer debug).
 */
export function resetQuota() {
  try {
    localStorage.removeItem(STORAGE_KEY_USED)
    localStorage.removeItem(STORAGE_KEY_STAGE)
  } catch {
    // Ignore
  }
  notifyQuotaChange()
}

/**
 * Detect if an error message or exception represents a model rate limit / 429 / ResourceExhausted.
 */
export function isRateLimitError(errOrMsg) {
  if (!errOrMsg) return false
  const msg = typeof errOrMsg === 'string' ? errOrMsg : (errOrMsg.message || String(errOrMsg))
  const lower = msg.toLowerCase()
  return (
    lower.includes('429') ||
    lower.includes('resourceexhausted') ||
    lower.includes('resource_exhausted') ||
    lower.includes('rate limit') ||
    lower.includes('ratelimit') ||
    lower.includes('too many requests') ||
    lower.includes('quota') ||
    lower.includes('model reached limit') ||
    lower.includes('failed to load model')
  )
}

/**
 * Format any model error: if rate limited, returns "This model reached limit".
 */
export function formatModelError(errOrMsg, fallback = 'Failed to generate answer from model.') {
  if (!errOrMsg) return fallback
  if (isRateLimitError(errOrMsg)) {
    return RATE_LIMIT_MESSAGE
  }
  const msg = typeof errOrMsg === 'string' ? errOrMsg : (errOrMsg.message || fallback)
  return msg
}

/**
 * React hook to observe and consume user quota in components.
 */
export function useQuota() {
  const [state, setState] = useState(() => {
    initRefreshBonus()
    return {
      used: getQuotaUsed(),
      remaining: getRemainingQuota(),
      stage: getRefreshStage(),
      maxQuota: getMaxQuota(),
      isExceeded: isQuotaExceeded(),
      studentMessage: getQuotaMessage(),
    }
  })

  const sync = useCallback(() => {
    initRefreshBonus()
    setState({
      used: getQuotaUsed(),
      remaining: getRemainingQuota(),
      stage: getRefreshStage(),
      maxQuota: getMaxQuota(),
      isExceeded: isQuotaExceeded(),
      studentMessage: getQuotaMessage(),
    })
  }, [])

  useEffect(() => {
    sync()
    if (typeof window !== 'undefined' && window.addEventListener) {
      window.addEventListener(EVENT_NAME, sync)
      window.addEventListener('storage', sync)
      return () => {
        window.removeEventListener(EVENT_NAME, sync)
        window.removeEventListener('storage', sync)
      }
    }
  }, [sync])

  const tryConsume = useCallback(() => {
    const res = consumeQuota()
    sync()
    return res
  }, [sync])

  return {
    used: state.used,
    remaining: state.remaining,
    isExceeded: state.isExceeded,
    maxQuota: state.maxQuota,
    stage: state.stage,
    studentMessage: state.studentMessage,
    consumeQuota: tryConsume,
    resetQuota,
  }
}
