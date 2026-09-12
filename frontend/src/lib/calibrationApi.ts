import type { CalibrationCapture, CalibrationDraft, CalibrationProfile, CalibrationRevision } from '../types/calibration'
const request = async <T>(path: string, init?: RequestInit): Promise<T> => { const response = await fetch(`/api/calibration${path}`, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...init }); if (!response.ok) throw new Error((await response.text()) || 'Calibration request failed'); return response.json() as Promise<T> }
export const listCalibrationProfiles = () => request<CalibrationProfile[]>('/profiles')
export const createCalibrationProfile = (draft: CalibrationDraft) => request<CalibrationRevision>('/profiles', { method: 'POST', body: JSON.stringify(draft) })
export const reviseCalibrationProfile = (id: string, draft: CalibrationDraft) => request<CalibrationRevision>(`/profiles/${id}/revisions`, { method: 'POST', body: JSON.stringify(draft) })
export const activateCalibrationRevision = (id: string) => request<CalibrationRevision>(`/revisions/${id}/activate`, { method: 'POST' })
export const captureCalibration = (device_id: string, cell_id: string) => request<CalibrationCapture>('/capture/optical', { method: 'POST', body: JSON.stringify({ device_id, cell_id }) })
