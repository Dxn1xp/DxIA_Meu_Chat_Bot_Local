/**
 * hooks/useBackendStatus.js
 * Faz polling do /health até o Assistant estar pronto,
 * depois carrega os detalhes do modelo via /status.
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { checkHealth, getStatus } from '../utils/api'

export function useBackendStatus() {
  const [state, setState] = useState('connecting') // connecting | starting | online | offline
  const [info, setInfo]   = useState(null)         // dados de /status
  const timerRef          = useRef(null)

  const poll = useCallback(async () => {
    try {
      const res = await checkHealth()
      if (res.ok) {
        setState('online')
        clearInterval(timerRef.current)
        // Carrega detalhes do modelo uma única vez
        getStatus().then(setInfo).catch(() => {})
      } else if (res.status === 503) {
        setState('starting')
      } else {
        setState('offline')
      }
    } catch {
      setState('offline')
    }
  }, [])

  useEffect(() => {
    poll()
    timerRef.current = setInterval(poll, 3000)
    return () => clearInterval(timerRef.current)
  }, [poll])

  const refresh = useCallback(() => {
    setState('connecting')
    clearInterval(timerRef.current)
    poll()
    timerRef.current = setInterval(poll, 3000)
  }, [poll])

  return { state, info, refresh }
}
