export type ExperimentState = 'draft' | 'ready' | 'starting' | 'running' | 'stopping' | 'completed' | 'aborted'
export type ExperimentMode = 'passive' | 'manual'

export interface ExperimentArm {
  id?: string
  device_id: string
  cell_id: string
  mode: ExperimentMode
  initial_led_pwm: number
  initial_mixer_on: boolean
  label?: string | null
}

export interface Experiment {
  id: string
  name: string
  state: ExperimentState
  description: string | null
  notes: string | null
  arms: ExperimentArm[]
}

export interface ExperimentInput {
  name: string
  description?: string
  arms: ExperimentArm[]
}
