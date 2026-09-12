import type { AnalyticsSeriesPoint } from '../../types/analytics'
import { ControlChart } from './ControlChart'
import { PowerChart } from './PowerChart'
export function SeriesSection({ points }: { points: AnalyticsSeriesPoint[] }) { return <section aria-labelledby="series-heading" className="grid gap-4"><h2 className="sr-only" id="series-heading">Experiment series</h2><PowerChart points={points} /><ControlChart points={points} /></section> }
