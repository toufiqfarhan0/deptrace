/**
 * User Quota and Rate Limit Manager for Veridex.
 * 
 * Enforces a maximum 3-interaction usage limit for Ask, Trace, and Entity queries,
 * with the message: "I don't have enough quota, I'm a student."
 * Also provides utilities to identify and format Gemini model rate-limit errors
 * as "This model reached limit".
 */

import { useState, useEffect, useCallback } from 'react'

export const MAX_QUOTA = 3
export const STORAGE_KEY = 'veridex_user_quota_count'
export const QUOTA_STUDENT_MESSAGE = "I don't have enough quota, I'm a student."
export const RATE_LIMIT_MESSAGE = 'This model reached limit'

const EVENT_NAME = 'veridex:quota-changed'

/**
 * Get current quota usage count from localStorage.
 */
export function getQuotaUsed() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
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
 * Get remaining actions/queries.
 */
export function getRemainingQuota() {
  const used = getQuotaUsed()
  return Math.max(0, MAX_QUOTA - used)
}

/**
 * Check if the user has reached or exceeded their 3-action quota.
 */
export function isQuotaExceeded() {
  return getQuotaUsed() >= MAX_QUOTA
}

/**
 * Dispatch an event to synchronize all listeners/components across tabs or in-page.
 */
function notifyQuotaChange() {
  if (typeof window !== 'undefined' && window.dispatchEvent) {
    try {
      window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: { used: getQuotaUsed() } }))
    } catch {
      // Ignore event dispatch errors
    }
  }
}

/**
 * Attempt to consume 1 quota unit.
 * Returns { allowed: true, remaining: number } if quota available,
 * or { allowed: false, remaining: 0, message: string } if exceeded.
 */
export function consumeQuota() {
  const current = getQuotaUsed()
  if (current >= MAX_QUOTA) {
    notifyQuotaChange()
    return {
      allowed: false,
      remaining: 0,
      message: QUOTA_STUDENT_MESSAGE,
    }
  }

  const next = current + 1
  try {
    localStorage.setItem(STORAGE_KEY, String(next))
  } catch {
    // Ignore localStorage failures
  }

  notifyQuotaChange()
  return {
    allowed: true,
    remaining: Math.max(0, MAX_QUOTA - next),
  }
}

/**
 * Reset quota (useful for testing or developer debug).
 */
export function resetQuota() {
  try {
    localStorage.removeItem(STORAGE_KEY)
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
 * Format any model error: if rate limited, returns "This model reached limit",
 * otherwise returns the original message or fallback.
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
  const [used, setUsed] = useState(getQuotaUsed)

  const sync = useCallback(() => {
    setUsed(getQuotaUsed())
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

  const remaining = Math.max(0, MAX_QUOTA - used)
  const exceeded = used >= MAX_QUOTA

  const tryConsume = useCallback(() => {
    const res = consumeQuota()
    setUsed(getQuotaUsed())
    return res
  }, [])

  return {
    used,
    remaining,
    isExceeded: exceeded,
    maxQuota: MAX_QUOTA,
    studentMessage: QUOTA_STUDENT_MESSAGE,
    consumeQuota: tryConsume,
    resetQuota,
  }
}
