export type ExperimentState = 'draft' | 'ready' | 'starting' | 'running' | 'stopping' | 'completed' | 'aborted'
export type ExperimentMode = 'passive' | 'manual' | 'adaptive'
export interface AdaptiveConfig { initial_pwm: number; pwm_min: number; pwm_max: number; pwm_step: number; settle_ms: number; minimum_valid_samples: number; objective_deadband_fraction: number; mixer_policy: 'off' | 'periodic'; mixer_period_ms?: number | null; mixer_on_ms?: number | null }

export interface ExperimentArm {
  id?: string
  device_id: string
  cell_id: string
  mode: ExperimentMode
  initial_led_pwm: number
  initial_mixer_on: boolean
  label?: string | null
  calibration_revision_id?: string | null
  adaptive?: AdaptiveConfig | null
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
