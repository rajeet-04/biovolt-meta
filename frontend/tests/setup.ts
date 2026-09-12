import '@testing-library/jest-dom/vitest'

// App lifecycle tests should not open a real socket to localhost.
class TestWebSocket {
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onmessage: ((event: { data: unknown }) => void) | null = null
  onerror: (() => void) | null = null

  constructor(_url: string) {}

  close(): void {
    this.onclose?.()
  }
}

globalThis.WebSocket = TestWebSocket as unknown as typeof WebSocket
