import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'

import { formatDuration, formatTimestamp } from '@/shared/lib/time'

const numberFormatter = new Intl.NumberFormat()

export default function ProgressPanel({ progress }) {
  if (!progress) return null
  const {
    status,
    percent,
    iterationsCompleted,
    iterationsTotal,
    iterationsRemaining,
    papersCollected,
    seedPapers,
    citations,
    references,
    startedAt,
    lastUpdate,
  } = progress

  const statusLabel =
    status === 'completed'
      ? 'Completed'
      : status === 'failed'
      ? 'Failed'
      : 'Running'

  const isActive = status === 'running'
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    if (!startedAt) return undefined
    if (!isActive) {
      setNow(lastUpdate || startedAt)
      return undefined
    }
    const interval = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(interval)
  }, [startedAt, isActive, lastUpdate])

  const startedAtText = startedAt ? formatTimestamp(startedAt) : '—'
  const lastUpdateText = formatTimestamp(lastUpdate || startedAt)
  const elapsedText = startedAt ? formatDuration(startedAt, isActive ? now : lastUpdate || now) : '—'

  const infoRows = [
    { label: 'Iterations completed', value: `${iterationsCompleted}/${iterationsTotal}` },
    { label: 'Iterations remaining', value: iterationsRemaining },
    { label: 'Papers collected', value: papersCollected },
    { label: 'Seed papers', value: seedPapers },
    { label: 'Citations collected', value: citations },
    { label: 'References collected', value: references },
  ]

  return (
    <section className="bg-white rounded-3xl border border-gray-200 shadow-sm p-6 space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Crawler progress</p>
          <div className="flex items-center gap-2">
            <h2 className="text-3xl font-semibold text-gray-900">{statusLabel}</h2>
            {status === 'running' ? <Loader2 className="w-5 h-5 text-gray-500 animate-spin" /> : null}
          </div>
          <p className="text-sm text-gray-600">
            Started {startedAtText || '—'} • Last update {lastUpdateText || '—'} • Elapsed {elapsedText || '—'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500 uppercase tracking-[0.3em]">Completion</p>
          <p className="text-4xl font-semibold text-gray-900">{percent}%</p>
        </div>
      </div>

      <div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gray-900 transition-all duration-300"
            style={{ width: `${percent}%` }}
          />
        </div>
        <p className="text-sm text-gray-600 mt-2">
          Iteration {Math.min(iterationsCompleted, iterationsTotal)} of {iterationsTotal}
        </p>
      </div>

      <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {infoRows.map((item) => (
          <div
            key={item.label}
            className="rounded-2xl border border-gray-100 bg-gray-50 p-4 shadow-sm"
          >
            <dt className="text-xs uppercase tracking-[0.3em] text-gray-500">{item.label}</dt>
            <dd className="text-xl font-semibold text-gray-900 mt-1">
              {typeof item.value === 'number' ? numberFormatter.format(item.value) : item.value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
