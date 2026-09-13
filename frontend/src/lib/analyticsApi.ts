import type { AnalyticsSeries, AnalyticsSummary, EnergyComparison } from '../types/analytics'
const get = async <T>(path: string): Promise<T> => { const response = await fetch(`/api/experiments${path}`, { credentials: 'include' }); if (!response.ok) throw new Error('Analytics unavailable'); return response.json() as Promise<T> }
export const getAnalyticsSummary = (id: string) => get<AnalyticsSummary>(`/${id}/analytics/summary`)
export const getAnalyticsComparison = (id: string, passiveArmId: string, adaptiveArmId: string) => get<EnergyComparison>(`/${id}/analytics/comparison?passive_arm_id=${encodeURIComponent(passiveArmId)}&adaptive_arm_id=${encodeURIComponent(adaptiveArmId)}`)
export const getAnalyticsSeries = (id: string, bucketSeconds = 10) => get<AnalyticsSeries>(`/${id}/analytics/series?bucket_seconds=${bucketSeconds}`)
