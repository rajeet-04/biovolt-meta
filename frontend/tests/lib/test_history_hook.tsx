import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useTelemetryHistory } from '../../src/hooks/useTelemetryHistory'
import * as api from '../../src/lib/api'

const mockedHistory = vi.spyOn(api, 'getTelemetryHistory')

beforeEach(() => {
  mockedHistory.mockReset()
})

describe('useTelemetryHistory', () => {
  it('does not fetch and remains empty when either source identity is absent', () => {
    const { result } = renderHook(() => useTelemetryHistory(null, 'cell-a', 25))

    expect(result.current.data).toEqual([])
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(mockedHistory).not.toHaveBeenCalled()
  })

  it('clamps requested history limits to the supported 1..1000 range', async () => {
    mockedHistory.mockResolvedValue([])
    const { result, rerender } = renderHook(
      ({ limit }: { limit: number }) => useTelemetryHistory('biovolt-01', 'cell-a', limit),
      { initialProps: { limit: 5_000 } },
    )

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(mockedHistory).toHaveBeenNthCalledWith(
      1,
      { deviceId: 'biovolt-01', cellId: 'cell-a', limit: 1_000 },
      expect.any(AbortSignal),
    )

    rerender({ limit: 0 })
    await waitFor(() => expect(mockedHistory).toHaveBeenCalledTimes(2))
    expect(mockedHistory).toHaveBeenNthCalledWith(
      2,
      { deviceId: 'biovolt-01', cellId: 'cell-a', limit: 1 },
      expect.any(AbortSignal),
    )
  })

  it('aborts the previous request when the source changes', async () => {
    const signals: AbortSignal[] = []
    mockedHistory.mockImplementation(
      (_query, signal) => {
        if (signal) signals.push(signal)
        return new Promise(() => {})
      },
    )

    const { rerender, unmount } = renderHook(
      ({ deviceId, cellId }: { deviceId: string; cellId: string }) =>
        useTelemetryHistory(deviceId, cellId, 25),
      { initialProps: { deviceId: 'biovolt-01', cellId: 'cell-a' } },
    )

    await waitFor(() => expect(signals).toHaveLength(1))
    rerender({ deviceId: 'hardware-02', cellId: 'cell-b' })
    await waitFor(() => expect(signals).toHaveLength(2))

    expect(signals[0]!.aborted).toBe(true)
    expect(signals[1]!.aborted).toBe(false)
    unmount()
    expect(signals[1]!.aborted).toBe(true)
  })

  it('exposes request failures', async () => {
    mockedHistory.mockRejectedValue(new Error('connection refused'))
    const { result } = renderHook(() => useTelemetryHistory('biovolt-01', 'cell-a', 25))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toEqual([])
    expect(result.current.error).toBe('connection refused')
  })
})
