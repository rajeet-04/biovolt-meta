interface MixerControlProps { on: boolean; disabled: boolean; onApply: (on: boolean) => void }

export function MixerControl({ on, disabled, onApply }: MixerControlProps) {
  return <section className="grid gap-2 rounded-lg border border-bio-border bg-bio-panel p-4"><h2 className="font-semibold text-bio-text">Mixer</h2><p className="text-sm text-bio-muted">Safety cooldown may reject a mixer start.</p><button className="w-fit rounded border border-bio-border px-3 py-2 text-sm text-bio-text" disabled={disabled} onClick={() => onApply(!on)} type="button">Turn mixer {on ? 'off' : 'on'}</button></section>
}
