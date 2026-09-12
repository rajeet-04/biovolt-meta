export interface DeviceSystemStatus {
  latest_telemetry_at: string | null
  latest_telemetry_age_ms: number | null
}

export interface SystemStatus {
  backend: 'ok'
  database: 'ok' | 'error'
  connected_devices: string[]
  device_count: number
  devices: Record<string, DeviceSystemStatus>
}
