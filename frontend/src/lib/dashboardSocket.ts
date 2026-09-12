import { isProcessedTelemetryV1, type ProcessedTelemetryV1 } from '../types/telemetry'

export interface DashboardSocketHandlers {
  onTelemetry(frame: ProcessedTelemetryV1): void
  onState(state: 'connecting' | 'connected' | 'disconnected'): void
  onInvalidMessage(raw: string): void
}

export interface DashboardWebSocket {
  onopen: (() => void) | null
  onclose: (() => void) | null
  onmessage: ((event: { data: unknown }) => void) | null
  onerror?: (() => void) | null
  close(): void
}

export type DashboardSocketFactory = (url: string) => DashboardWebSocket

export interface DashboardSocketOptions {
  socketFactory?: DashboardSocketFactory
  location?: Pick<Location, 'protocol' | 'host'>
}

/** Return the bounded delay before the given reconnect attempt. */
export function reconnectDelay(attempt: number): number {
  const normalizedAttempt = Math.max(0, Math.floor(attempt))
  return Math.min(1_000 * 2 ** normalizedAttempt, 10_000)
}

/** Build the same-origin WebSocket URL used by the dashboard. */
export function dashboardSocketUrl(
  location: Pick<Location, 'protocol' | 'host'> = window.location,
): string {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${location.host}/ws/dashboard`
}

function browserSocketFactory(url: string): DashboardWebSocket {
  return new WebSocket(url) as unknown as DashboardWebSocket
}

export class DashboardSocketClient {
  private readonly handlers: DashboardSocketHandlers
  private readonly socketFactory: DashboardSocketFactory
  private readonly location: Pick<Location, 'protocol' | 'host'> | undefined
  private socket: DashboardWebSocket | null = null
  private reconnectTimer: number | null = null
  private reconnectAttempt = 0
  private stopped = true

  constructor(handlers: DashboardSocketHandlers, options: DashboardSocketOptions = {}) {
    this.handlers = handlers
    this.socketFactory = options.socketFactory ?? browserSocketFactory
    this.location = options.location
  }

  start(): void {
    if (!this.stopped) return

    this.stopped = false
    this.reconnectAttempt = 0
    this.handlers.onState('connecting')
    this.connect()
  }

  stop(): void {
    const wasRunning = !this.stopped
    this.stopped = true

    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    const socket = this.socket
    this.socket = null
    if (socket !== null) {
      socket.onopen = null
      socket.onmessage = null
      socket.onclose = null
      socket.close()
      // Some browser WebSocket implementations clear handlers during close;
      // keep late connection errors from becoming uncaught after unmount.
      socket.onerror = () => undefined
    }

    if (wasRunning) this.handlers.onState('disconnected')
  }

  private connect(): void {
    if (this.stopped || this.socket !== null) return

    let socket: DashboardWebSocket
    try {
      socket = this.socketFactory(dashboardSocketUrl(this.location))
    } catch {
      this.handlers.onState('disconnected')
      this.scheduleReconnect()
      return
    }

    this.socket = socket
    // The close callback owns reconnect state; consume browser error events.
    socket.onerror = () => undefined
    socket.onopen = () => {
      if (this.socket !== socket || this.stopped) return
      this.reconnectAttempt = 0
      this.handlers.onState('connected')
    }
    socket.onmessage = (event) => {
      if (this.socket !== socket || this.stopped) return
      this.handleMessage(event.data)
    }
    socket.onclose = () => {
      if (this.socket !== socket) return
      this.socket = null
      if (this.stopped) return
      this.handlers.onState('disconnected')
      this.scheduleReconnect()
    }
  }

  private handleMessage(data: unknown): void {
    const raw = typeof data === 'string' ? data : String(data)
    try {
      const parsed: unknown = JSON.parse(raw)
      if (isProcessedTelemetryV1(parsed)) {
        this.handlers.onTelemetry(parsed)
      } else {
        this.handlers.onInvalidMessage(raw)
      }
    } catch {
      this.handlers.onInvalidMessage(raw)
    }
  }

  private scheduleReconnect(): void {
    if (this.stopped || this.reconnectTimer !== null) return

    const delay = reconnectDelay(this.reconnectAttempt)
    this.reconnectAttempt += 1
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      if (this.stopped) return
      this.handlers.onState('connecting')
      this.connect()
    }, delay)
  }
}
