export type ControlMode = 'monitor' | 'passive' | 'adaptive' | 'manual'

export interface ProcessedTelemetryV1 {
  schema_version: 1
  device_id: string
  cell_id: string
  sequence: number
  timestamp: string
  electrical: {
    voltage_mv: number | null
    current_ua: number | null
    power_uw: number | null
    load_resistance_ohm: number
    cumulative_energy_mj: number | null
  }
  biological: {
    od680: number | null
    biomass_g_l: number | null
    biomass_total_g: number | null
    biomass_delta_g: number | null
    co2_biofixed_g: number | null
  }
  environment: {
    temperature_c: number | null
    lux: number | null
  }
  actuators: {
    grow_led_pwm: number
    mixer_on: boolean
  }
  control: {
    mode: ControlMode
  }
}

type UnknownRecord = Record<string, unknown>

export function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

export function isNullableNumber(value: unknown): value is number | null {
  return value === null || isFiniteNumber(value)
}

function hasExactKeys(value: UnknownRecord, keys: readonly string[]): boolean {
  const actual = Object.keys(value)
  return actual.length === keys.length && keys.every((key) => Object.hasOwn(value, key))
}

function isBoundedString(value: unknown, maxLength: number): value is string {
  return typeof value === 'string' && value.length >= 1 && value.length <= maxLength
}

function isNonNegativeNumber(value: unknown): value is number {
  return isFiniteNumber(value) && value >= 0
}

function isNullableNonNegativeNumber(value: unknown): value is number | null {
  return value === null || isNonNegativeNumber(value)
}

function isDateTime(value: unknown): value is string {
  if (
    typeof value !== 'string' ||
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)
  ) {
    return false
  }
  return Number.isFinite(Date.parse(value))
}

const telemetryKeys = [
  'schema_version',
  'device_id',
  'cell_id',
  'sequence',
  'timestamp',
  'electrical',
  'biological',
  'environment',
  'actuators',
  'control',
] as const

const electricalKeys = [
  'voltage_mv',
  'current_ua',
  'power_uw',
  'load_resistance_ohm',
  'cumulative_energy_mj',
] as const

const biologicalKeys = [
  'od680',
  'biomass_g_l',
  'biomass_total_g',
  'biomass_delta_g',
  'co2_biofixed_g',
] as const

const environmentKeys = ['temperature_c', 'lux'] as const
const actuatorKeys = ['grow_led_pwm', 'mixer_on'] as const
const controlKeys = ['mode'] as const

function isElectrical(value: unknown): boolean {
  if (!isRecord(value) || !hasExactKeys(value, electricalKeys)) return false

  return (
    isNullableNumber(value.voltage_mv) &&
    isNullableNumber(value.current_ua) &&
    isNullableNumber(value.power_uw) &&
    isFiniteNumber(value.load_resistance_ohm) &&
    value.load_resistance_ohm > 0 &&
    isNullableNonNegativeNumber(value.cumulative_energy_mj)
  )
}

function isBiological(value: unknown): boolean {
  if (!isRecord(value) || !hasExactKeys(value, biologicalKeys)) return false

  return (
    isNullableNonNegativeNumber(value.od680) &&
    isNullableNonNegativeNumber(value.biomass_g_l) &&
    isNullableNonNegativeNumber(value.biomass_total_g) &&
    isNullableNumber(value.biomass_delta_g) &&
    isNullableNonNegativeNumber(value.co2_biofixed_g)
  )
}

function isEnvironment(value: unknown): boolean {
  if (!isRecord(value) || !hasExactKeys(value, environmentKeys)) return false

  return isNullableNumber(value.temperature_c) && isNullableNonNegativeNumber(value.lux)
}

function isActuators(value: unknown): boolean {
  if (!isRecord(value) || !hasExactKeys(value, actuatorKeys)) return false

  return (
    isFiniteNumber(value.grow_led_pwm) &&
    Number.isInteger(value.grow_led_pwm) &&
    value.grow_led_pwm >= 0 &&
    value.grow_led_pwm <= 255 &&
    typeof value.mixer_on === 'boolean'
  )
}

function isControl(value: unknown): boolean {
  if (!isRecord(value) || !hasExactKeys(value, controlKeys)) return false

  return value.mode === 'monitor' || value.mode === 'passive' || value.mode === 'adaptive' || value.mode === 'manual'
}

export function isProcessedTelemetryV1(value: unknown): value is ProcessedTelemetryV1 {
  if (!isRecord(value) || !hasExactKeys(value, telemetryKeys)) return false

  return (
    value.schema_version === 1 &&
    isBoundedString(value.device_id, 64) &&
    isBoundedString(value.cell_id, 64) &&
    isFiniteNumber(value.sequence) &&
    Number.isInteger(value.sequence) &&
    value.sequence >= 0 &&
    isDateTime(value.timestamp) &&
    isElectrical(value.electrical) &&
    isBiological(value.biological) &&
    isEnvironment(value.environment) &&
    isActuators(value.actuators) &&
    isControl(value.control)
  )
}
