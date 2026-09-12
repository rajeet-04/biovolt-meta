import { registerSW } from 'virtual:pwa-register'

export interface PwaUpdateState {
  needRefresh: boolean
  offlineReady: boolean
}

export interface PwaRegistration {
  getState(): PwaUpdateState
  update(): Promise<void>
}

/** Register the shell service worker without forcing a telemetry-view reload. */
export function registerPwa(onStateChange?: (state: PwaUpdateState) => void): PwaRegistration {
  let state: PwaUpdateState = { needRefresh: false, offlineReady: false }
  const notify = (next: PwaUpdateState): void => {
    state = next
    onStateChange?.(state)
  }
  const updateServiceWorker = registerSW({
    immediate: true,
    onNeedRefresh: () => notify({ ...state, needRefresh: true }),
    onOfflineReady: () => notify({ ...state, offlineReady: true }),
  })

  return {
    getState: () => state,
    update: () => updateServiceWorker(false),
  }
}
