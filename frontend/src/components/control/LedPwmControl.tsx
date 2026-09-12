interface LedPwmControlProps { value: number; disabled: boolean; onChange: (value: number) => void; onApply: () => void }

export function LedPwmControl({ value, disabled, onChange, onApply }: LedPwmControlProps) {
  return <section className="grid gap-2 rounded-lg border border-bio-border bg-bio-panel p-4"><h2 className="font-semibold text-bio-text">Grow LED PWM</h2><input aria-label="Desired LED PWM" disabled={disabled} max={255} min={0} onChange={(event) => onChange(Number(event.target.value))} type="range" value={value} /><output>{value}</output><button className="w-fit rounded bg-bio-accent px-3 py-2 text-sm font-semibold text-bio-bg" disabled={disabled} onClick={onApply} type="button">Apply LED setting</button></section>
}
