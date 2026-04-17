import { useEffect, useRef, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'
import { useAuthStore } from '../store/authStore'

type EventCallback = (data: unknown) => void

export function useWebSocket() {
  const socketRef = useRef<Socket | null>(null)
  const { token } = useAuthStore()
  const callbacksRef = useRef<Map<string, EventCallback[]>>(new Map())

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || ''

    socketRef.current = io(wsUrl, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
    })

    socketRef.current.on('connect', () => {
      console.log('[WS] Connected:', socketRef.current?.id)
    })

    socketRef.current.on('disconnect', () => {
      console.log('[WS] Disconnected')
    })

    socketRef.current.on('connect_error', (err) => {
      console.warn('[WS] Connection error:', err.message)
    })

    // Re-attach registered callbacks
    callbacksRef.current.forEach((cbs, event) => {
      cbs.forEach((cb) => socketRef.current?.on(event, cb))
    })

    return () => {
      socketRef.current?.disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  const on = useCallback((event: string, callback: EventCallback) => {
    if (!callbacksRef.current.has(event)) {
      callbacksRef.current.set(event, [])
    }
    callbacksRef.current.get(event)!.push(callback)
    socketRef.current?.on(event, callback)
  }, [])

  const off = useCallback((event: string, callback: EventCallback) => {
    const cbs = callbacksRef.current.get(event) ?? []
    callbacksRef.current.set(event, cbs.filter((cb) => cb !== callback))
    socketRef.current?.off(event, callback)
  }, [])

  const emit = useCallback((event: string, data?: unknown) => {
    socketRef.current?.emit(event, data)
  }, [])

  return { on, off, emit, socket: socketRef.current }
}
