import { useEffect, useMemo, useState } from 'react'
import { OperatorLoginDialog } from '../components/operator/OperatorLoginDialog'
import { CommandStatus } from '../components/control/CommandStatus'
import { LedPwmControl } from '../components/control/LedPwmControl'
import { MixerControl } from '../components/control/MixerControl'
import { getCommand, sendControlCommand, type CommandRecord } from '../lib/controlApi'
import { isTelemetryStale } from '../lib/stale'
import { useOperatorStore } from '../stores/operatorStore'
import { useTelemetryStore } from '../stores/telemetryStore'
import { useOnlineStatus } from '../hooks/useOnlineStatus'

export function ControlPage() {
  const { authenticated } = useOperatorStore()
  const { sources, selectedSource, wsState } = useTelemetryStore()
  const latest = selectedSource ? sources[selectedSource]?.latest : Object.values(sources)[0]?.latest
  const [desiredPwm, setDesiredPwm] = useState(() => latest?.actuators.grow_led_pwm ?? 0)
  const [command, setCommand] = useState<CommandRecord | null>(null)
  const [loginOpen, setLoginOpen] = useState(false)
  const [clockMs, setClockMs] = useState(() => Date.now())
  useEffect(() => {
    const timer = window.setInterval(() => setClockMs(Date.now()), 250)
    return () => window.clearInterval(timer)
  }, [])
  const online = useOnlineStatus()
  const stale = latest ? isTelemetryStale(latest.timestamp, clockMs) : true
  const disabledReason = !online ? 'Browser is offline.' : wsState !== 'connected' ? 'Backend dashboard is disconnected.' : stale ? 'Selected device is stale.' : !authenticated ? 'Authenticate to control hardware.' : null
  const disabled = disabledReason !== null
  const deviceId = latest?.device_id ?? 'biovolt-01'

  useEffect(() => {
    if (!command?.command_id || ['applied', 'rejected', 'failed', 'expired'].includes(command.status)) return
    let active = true
    const poll = window.setInterval(() => {
      void getCommand(command.command_id).then((next) => { if (active) setCommand(next) }).catch(() => undefined)
    }, 500)
    return () => { active = false; window.clearInterval(poll) }
  }, [command])

  const send = async (kind: string, payload: Record<string, unknown>) => {
    if (!authenticated) { setLoginOpen(true); return }
    try { setCommand(await sendControlCommand({ device_id: deviceId, kind, payload })) } catch { setCommand({ command_id: '', device_id: deviceId, status: 'failed', kind, reason_code: 'internal_error', message: 'Unable to send command', applied_state: null }) }
  }
  const confirmedPwm = useMemo(() => latest?.actuators.grow_led_pwm ?? 0, [latest])
  return <div className="mx-auto grid max-w-4xl gap-6"><div><h1 className="text-3xl font-semibold text-bio-text">Manual control</h1><p className="mt-2 text-bio-muted">Desired values never become confirmed until the device acknowledges application.</p></div>{disabledReason ? <p className="rounded border border-bio-border p-3 text-sm text-bio-muted" role="status">{disabledReason}</p> : null}<p className="text-sm text-bio-muted">Confirmed LED PWM: {confirmedPwm}</p><LedPwmControl disabled={disabled} onApply={() => void send('set_led_pwm', { pwm: desiredPwm })} onChange={setDesiredPwm} value={desiredPwm} /><MixerControl disabled={disabled} on={latest?.actuators.mixer_on ?? false} onApply={(on) => void send('set_mixer', { on })} /><button className="w-fit rounded border border-red-400 px-4 py-2 text-sm font-semibold text-red-300" disabled={disabled} onClick={() => void send('safe_stop', {})} type="button">Safe Stop</button><CommandStatus command={command} /><OperatorLoginDialog onClose={() => setLoginOpen(false)} open={loginOpen} /></div>
}
