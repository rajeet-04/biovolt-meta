import { useState } from 'react'
import type { ExperimentArm, ExperimentInput } from '../../types/experiments'
import { AdaptiveConfigForm } from './AdaptiveConfigForm'

const emptyArm = (): ExperimentArm => ({
  device_id: '',
  cell_id: '',
  mode: 'passive',
  initial_led_pwm: 0,
  initial_mixer_on: false,
  adaptive: null,
})

interface ExperimentFormProps {
  onSubmit: (input: ExperimentInput) => Promise<void> | void
}

export function ExperimentForm({ onSubmit }: ExperimentFormProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [arms, setArms] = useState<ExperimentArm[]>([emptyArm()])
  const [error, setError] = useState<string | null>(null)

  return (
    <form
      className="grid gap-4 rounded-lg border border-bio-border bg-bio-panel p-5"
      onSubmit={(event) => {
        event.preventDefault()
        if (!name.trim() || arms.some((arm) => !arm.device_id.trim() || !arm.cell_id.trim())) {
          setError('Name, device, cell, and at least one complete arm are required.')
          return
        }
        setError(null)
        const input = { name: name.trim(), arms }
        void onSubmit(description.trim() ? { ...input, description: description.trim() } : input)
      }}
    >
      <h2 className="text-xl font-semibold text-bio-text">New experiment</h2>
      <label className="grid gap-1 text-sm text-bio-text">
        Name
        <input className="rounded border border-bio-border bg-bio-panel-strong px-3 py-2" onChange={(event) => setName(event.target.value)} value={name} />
      </label>
      <label className="grid gap-1 text-sm text-bio-text">
        Description (optional)
        <textarea className="rounded border border-bio-border bg-bio-panel-strong px-3 py-2" onChange={(event) => setDescription(event.target.value)} value={description} />
      </label>
      {arms.map((arm, index) => (
        <fieldset className="grid gap-2 rounded border border-bio-border p-3" key={index}>
          <legend className="px-1 text-sm text-bio-muted">Arm {index + 1}</legend>
          <label className="text-sm text-bio-text">Device<input aria-label={`Device ${index + 1}`} className="mt-1 block w-full rounded border border-bio-border bg-bio-panel-strong px-3 py-2" onChange={(event) => setArms((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, device_id: event.target.value } : item))} value={arm.device_id} /></label>
          <label className="text-sm text-bio-text">Cell<input aria-label={`Cell ${index + 1}`} className="mt-1 block w-full rounded border border-bio-border bg-bio-panel-strong px-3 py-2" onChange={(event) => setArms((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, cell_id: event.target.value } : item))} value={arm.cell_id} /></label>
          <label className="text-sm text-bio-text">Mode<select aria-label={`Mode ${index + 1}`} className="mt-1 block rounded border border-bio-border bg-bio-panel-strong px-3 py-2" onChange={(event) => setArms((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, mode: event.target.value as ExperimentArm['mode'], initial_mixer_on: event.target.value === 'manual' ? item.initial_mixer_on : false, adaptive: event.target.value === 'adaptive' ? (item.adaptive ?? { initial_pwm: item.initial_led_pwm, pwm_min: 0, pwm_max: 255, pwm_step: 4, settle_ms: 3000, minimum_valid_samples: 3, objective_deadband_fraction: 0.01, mixer_policy: 'off' }) : null } : item))} value={arm.mode}><option value="passive">Passive</option><option value="manual">Manual</option><option value="adaptive">Adaptive</option></select></label>
          <label className="text-sm text-bio-text">Initial LED PWM<input aria-label={`Initial LED PWM ${index + 1}`} className="mt-1 block rounded border border-bio-border bg-bio-panel-strong px-3 py-2" max={255} min={0} onChange={(event) => setArms((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, initial_led_pwm: Number(event.target.value) } : item))} type="number" value={arm.initial_led_pwm} /></label>
          {arm.mode === 'manual' ? <label className="flex gap-2 text-sm text-bio-text"><input checked={arm.initial_mixer_on} onChange={(event) => setArms((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, initial_mixer_on: event.target.checked } : item))} type="checkbox" /> Initial mixer on</label> : null}
          {arm.mode === 'adaptive' && arm.adaptive ? <AdaptiveConfigForm onChange={(adaptive) => setArms((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, adaptive, initial_led_pwm: adaptive.initial_pwm } : item))} value={arm.adaptive} /> : null}
        </fieldset>
      ))}
      <button className="w-fit rounded bg-bio-panel-strong px-3 py-2 text-sm text-bio-text" onClick={() => setArms((current) => [...current, emptyArm()])} type="button">Add arm</button>
      {error ? <p className="text-sm text-red-300" role="alert">{error}</p> : null}
      <button className="w-fit rounded bg-bio-accent px-4 py-2 text-sm font-semibold text-bio-bg" type="submit">Create experiment</button>
    </form>
  )
}
