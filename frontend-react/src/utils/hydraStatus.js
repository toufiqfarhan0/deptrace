/**
 * HydraDB Status Helper for Veridex UI (Step 18A).
 * 
 * Accurately parses and formats the connection state from /api/health:
 * - Loading: { status: 'loading', ... } -> 'CONNECTING...'
 * - Cloud: { status: 'ok', hydradb: 'ok (cloud: veridex-hackhydra)' } -> 'HYDRADB CLOUD  CONNECTED'
 * - Local: { status: 'ok', hydradb: 'ok' } -> 'HYDRADB LOCAL  CONNECTED'
 * - Offline / Error: { status: 'degraded' | 'error', ... } -> 'HYDRADB OFFLINE'
 */

export function isHydraOnline(hydraStatus) {
  if (!hydraStatus) return false
  if (hydraStatus.status === 'loading') return false
  if (hydraStatus.status === 'ok') return true
  if (typeof hydraStatus.hydradb === 'string' && hydraStatus.hydradb.startsWith('ok')) return true
  return false
}

export function getHydraStatusMode(hydraStatus) {
  if (!hydraStatus || hydraStatus.status === 'loading') return 'loading'
  const isOnline = isHydraOnline(hydraStatus)
  if (!isOnline) return 'error'

  const hydradbStr = typeof hydraStatus.hydradb === 'string' ? hydraStatus.hydradb.toLowerCase() : ''
  if (hydradbStr.includes('cloud') || hydradbStr.includes('veridex-hackhydra')) {
    return 'cloud'
  }
  return 'local'
}

export function getHydraDotClass(hydraStatus) {
  const mode = getHydraStatusMode(hydraStatus)
  if (mode === 'loading') return 'loading'
  if (mode === 'cloud' || mode === 'local') return 'ok'
  return 'err'
}

export function getHydraStatusLabel(hydraStatus, options = {}) {
  const mode = getHydraStatusMode(hydraStatus)
  const format = options.format || 'header' // 'header' | 'sidebar' | 'landing' | 'health' | 'compact'

  switch (mode) {
    case 'loading':
      if (format === 'sidebar') return 'Checking HydraDB...'
      return 'CONNECTING...'

    case 'cloud':
      if (format === 'sidebar') return 'HydraDB Cloud Connected'
      if (format === 'health') return 'ONLINE (HYDRADB CLOUD)'
      if (format === 'compact') return 'HYDRADB CLOUD'
      return 'HYDRADB CLOUD  CONNECTED'

    case 'local':
      if (format === 'sidebar') return 'HydraDB Local Connected'
      if (format === 'health') return 'ONLINE (LOCAL)'
      if (format === 'compact') return 'HYDRADB LOCAL'
      return 'HYDRADB LOCAL  CONNECTED'

    case 'error':
    default:
      if (format === 'sidebar') return 'HydraDB Offline'
      if (format === 'health') return 'OFFLINE'
      return 'HYDRADB OFFLINE'
  }
}

export function getHydraAriaLabel(hydraStatus) {
  const mode = getHydraStatusMode(hydraStatus)
  switch (mode) {
    case 'loading': return 'Connecting to HydraDB'
    case 'cloud': return 'HydraDB Cloud connected'
    case 'local': return 'HydraDB Local connected'
    case 'error':
    default: return 'HydraDB is offline'
  }
}
