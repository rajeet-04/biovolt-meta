import { create } from 'zustand'
import { getOperatorSession, loginOperator, logoutOperator } from '../lib/operatorApi'
import type { OperatorSession } from '../types/operator'

interface OperatorStore extends OperatorSession {
  loading: boolean
  error: string | null
  load(): Promise<void>
  login(pin: string): Promise<boolean>
  logout(): Promise<void>
}

export const useOperatorStore = create<OperatorStore>((set) => ({
  authenticated: false,
  expiresAt: null,
  loading: false,
  error: null,
  load: async () => {
    set({ loading: true, error: null })
    try {
      const session = await getOperatorSession()
      set({ ...session, loading: false })
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Unable to load operator session' })
    }
  },
  login: async (pin) => {
    set({ loading: true, error: null })
    try {
      const session = await loginOperator(pin)
      set({ ...session, loading: false })
      return session.authenticated
    } catch (_error) {
      set({ authenticated: false, expiresAt: null, loading: false, error: 'Invalid operator PIN' })
      return false
    }
  },
  logout: async () => {
    try {
      const session = await logoutOperator()
      set({ ...session, error: null })
    } catch {
      set({ authenticated: false, expiresAt: null })
    }
  },
}))
