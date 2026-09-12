import { renderHook, waitFor } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import * as api from '../../src/lib/api'
import { useTelemetryHistory } from '../../src/hooks/useTelemetryHistory'

const mocked = vi.spyOn(api, 'getTelemetryHistory')
beforeEach(() => { mocked.mockReset() })

it('does not fetch when source is absent', async () => { const { result } = renderHook(() => useTelemetryHistory(null, null, 10)); await waitFor(() => expect(result.current.data).toEqual([])); expect(mocked).not.toHaveBeenCalled() })
it('clamps the requested history limit', async () => { mocked.mockResolvedValue([]); renderHook(() => useTelemetryHistory('device', 'cell', 9999)); await waitFor(() => expect(mocked).toHaveBeenCalledWith({ deviceId: 'device', cellId: 'cell', limit: 1000 }, expect.any(AbortSignal))) })
