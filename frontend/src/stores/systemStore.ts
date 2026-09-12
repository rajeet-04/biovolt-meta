import { create } from 'zustand'
import { fetchCapabilities } from '../api/capabilities'
import type { Capabilities } from '../types/capabilities'

interface SystemStore { capabilities: Capabilities | null; loading: boolean; error: string | null; loadCapabilities: () => Promise<void> }
export const useSystemStore = create<SystemStore>((set) => ({
  capabilities: null,
  loading: false,
  error: null,
  loadCapabilities: async () => {
    set({ loading: true, error: null, capabilities: null })
    try { set({ capabilities: await fetchCapabilities(), loading: false }) } catch (error) { set({ loading: false, error: error instanceof Error ? error.message : 'Capabilities unavailable', capabilities: null }) }
  },
}))
