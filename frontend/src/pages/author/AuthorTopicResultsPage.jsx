import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart3, ChevronDown, ChevronUp, Grid2x2, Layers, TrendingDown, TrendingUp } from 'lucide-react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  AreaChart,
  Area,
} from 'recharts'

import Stepper from '@/components/Stepper'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { loadAuthorTopicResult, loadSelectedAuthor, clearAuthorTopicResult } from './storage'
import { clearSession } from '@/shared/lib/session'

export default function AuthorTopicResultsPage() {
  const navigate = useNavigate()
  const [author, setAuthor] = useState(() => loadSelectedAuthor())
  const [result, setResult] = useState(() => loadAuthorTopicResult())
  const [visualizationsOpen, setVisualizationsOpen] = useState(true)

  const topicLabels = useMemo(() => result?.topic_labels || [], [result])
  const periodLabels = useMemo(() => result?.period_labels || [], [result])
  const periodCounts = useMemo(() => result?.periods || [], [result])
  const chartData = useMemo(() => {
    if (!result?.topic_proportions?.length) return []
    return result.topic_proportions.map((row, idx) => {
      const entry = {
        period: periodLabels[idx] || `Period ${idx + 1}`,
      }
      row.forEach((value, tIdx) => {
        const key = topicLabels[tIdx] || `Topic ${tIdx + 1}`
        entry[key] = value
      })
      return entry
    })
  }, [result, topicLabels, periodLabels])

  useEffect(() => {
    if (!author) {
      navigate('/author-topic-evolution/select')
    } else if (!result) {
      navigate('/author-topic-evolution/configure')
    }
  }, [author, result, navigate])

  if (!author || !result) return null

  const stats = [
    { label: 'Topics modeled', value: result.topic_labels?.length || result.num_topics },
    { label: 'Total papers analyzed', value: result.total_papers?.toLocaleString() },
    { label: 'Time span', value: buildTimeSpan(result.period_labels) },
  ]

  const finishFlow = () => {
    clearAuthorTopicResult()
    clearSession()
    navigate('/')
  }

  return (
    <div className="min-h-[calc(100vh-160px)] bg-white">
      <div className="max-w-6xl mx-auto px-6 py-10 space-y-8">
        <Stepper
          steps={['Select author', 'Configure', 'Analyze', 'Results']}
          currentStep={4}
        />

        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-100 pb-6">
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.4em] text-gray-500">Author topic evolution</p>
            <h1 className="text-4xl font-bold text-gray-900">Analysis results</h1>
            <p className="text-lg text-gray-600">
              Review the summary, topic breakdown, and saved artifacts for {author.name}.
            </p>
          </div>
          <Button
            className="rounded-full bg-gray-900 text-white hover:bg-gray-800"
            onClick={finishFlow}
          >
            Finish
          </Button>
        </div>

        <AnalysisSummaryCard
          author={author}
          stats={stats}
        />

        <PeriodCountsCard periods={periodCounts} />

        <TopicsIdentifiedCard topics={result.topic_labels} />

        <TrendCards
          emerging={result.emerging_topics}
          declining={result.declining_topics}
        />

        <VisualizationsAccordion
          open={visualizationsOpen}
          onToggle={() => setVisualizationsOpen((prev) => !prev)}
          chartData={chartData}
          topics={topicLabels}
          visualizationPath={result.visualization_path}
        />

        {!result.is_temporary && (
          <VisualizationLocationCard
            visualizationPath={result.visualization_path}
            libraryPath={result.library_path}
          />
        )}
      </div>
    </div>
  )
}

function AnalysisSummaryCard({ author, stats }) {
  return (
    <Card className="border-gray-200 rounded-3xl shadow-sm">
      <CardHeader>
        <CardTitle className="text-2xl text-gray-900">Analysis summary</CardTitle>
        <p className="text-sm text-gray-500">A quick snapshot of the run you just completed.</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700 flex flex-wrap items-center gap-3">
          <span className="text-lg font-semibold text-gray-900">{author.name}</span>
          <span className="text-xs font-semibold uppercase tracking-[0.3em] text-gray-500">{author.id}</span>
          <span>{author.works_count?.toLocaleString()} works · {author.cited_by_count?.toLocaleString()} citations</span>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {stats.map(({ label, value }) => (
            <div
              key={label}
              className="rounded-2xl border border-gray-200 bg-white px-4 py-5"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{value || '—'}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function TopicsIdentifiedCard({ topics }) {
  return (
    <Card className="border-gray-200 rounded-3xl shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-2xl text-gray-900">Topics identified</CardTitle>
        <p className="text-sm text-gray-500">Full list of modeled topics.</p>
      </CardHeader>
      <CardContent className="pt-2">
        {topics?.length ? (
          <div className="flex flex-wrap gap-2">
            {topics.map((topic) => (
              <span
                key={topic}
                className="rounded-full border border-gray-200 px-3 py-1 text-sm text-gray-700"
              >
                {topic}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">No topics recorded.</p>
        )}
      </CardContent>
    </Card>
  )
}

function TrendCards({ emerging, declining }) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <TrendCard
        icon={TrendingUp}
        label="Emerging topics"
        topics={emerging}
        accent="text-emerald-600"
      />
      <TrendCard
        icon={TrendingDown}
        label="Declining topics"
        topics={declining}
        accent="text-rose-600"
      />
    </div>
  )
}

function TrendCard({ icon: Icon, label, topics, accent }) {
  return (
    <div className="rounded-3xl border border-gray-200 bg-white p-6 space-y-3 shadow-sm">
      <p className={`flex items-center gap-3 text-sm font-semibold text-gray-800`}>
        <Icon className={`h-4 w-4 ${accent}`} />
        {label}
      </p>
      {topics?.length ? (
        <ul className="list-inside list-disc space-y-1 text-sm text-gray-700">
          {topics.map((topic) => (
            <li key={topic}>{topic}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-500">No clear signal.</p>
      )}
    </div>
  )
}

function VisualizationsAccordion({ open, onToggle, chartData, topics, visualizationPath }) {
  const hasData = chartData.length && topics.length
  const visualizationTabs = [
    { key: 'line', label: 'Line chart', description: 'Topic shares plotted across time.', component: VisualizationLineChart },
    { key: 'heatmap', label: 'Heatmap', description: 'Matrix of topic strength by period.', component: TopicHeatmap },
    { key: 'stacked', label: 'Stacked area', description: 'Stacked view of topic composition.', component: VisualizationStackedArea },
  ]
  const [activeTab, setActiveTab] = useState('line')
  const ActiveComponent = visualizationTabs.find((tab) => tab.key === activeTab)?.component || VisualizationLineChart

  return (
    <Card className="border-gray-200 rounded-3xl shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-2xl text-gray-900">Visualizations</CardTitle>
          <p className="text-sm text-gray-500">Expand to review available figure types.</p>
        </div>
        <Button
          variant="ghost"
          className="text-gray-600 hover:text-gray-900"
          onClick={onToggle}
        >
          {open ? (
            <>
              <ChevronUp className="mr-2 h-4 w-4" />
              Collapse
            </>
          ) : (
            <>
              <ChevronDown className="mr-2 h-4 w-4" />
              Expand
            </>
          )}
        </Button>
      </CardHeader>
      {open && (
        <CardContent className="space-y-6">
          {hasData ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-3">
                {visualizationTabs.map((tab) => (
                  <Button
                    key={tab.key}
                    variant={tab.key === activeTab ? 'default' : 'outline'}
                    className={`rounded-full ${tab.key === activeTab ? 'bg-gray-900 text-white hover:bg-gray-800' : 'border-gray-300 text-gray-700'}`}
                    onClick={() => setActiveTab(tab.key)}
                  >
                    {tab.label}
                  </Button>
                ))}
              </div>

              <VisualizationPanel
                title={visualizationTabs.find((tab) => tab.key === activeTab)?.label}
                description={visualizationTabs.find((tab) => tab.key === activeTab)?.description}
                footerPath={visualizationPath}
              >
                <ActiveComponent data={chartData} topics={topics} />
              </VisualizationPanel>
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              Not enough topic distribution data to render charts. Rerun the analysis to regenerate metadata.
            </p>
          )}
        </CardContent>
      )}
    </Card>
  )
}

function VisualizationPanel({ title, description, children, footerPath }) {
  return (
    <div className="rounded-3xl border border-gray-200 bg-white p-4 space-y-3 shadow-sm">
      <div>
        <p className="text-lg font-semibold text-gray-900">{title}</p>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
      <div className="border border-gray-100 rounded-2xl p-4 bg-gray-50">{children}</div>
      {footerPath && (
        <p className="text-xs text-gray-500">Exported figure path: <span className="text-gray-400">{footerPath}</span></p>
      )}
    </div>
  )
}

const CHART_COLORS = ['#2563eb', '#16a34a', '#ea580c', '#db2777', '#0f766e', '#9333ea', '#dc2626', '#0284c7', '#ca8a04']

function VisualizationLineChart({ data, topics }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis dataKey="period" tick={{ fill: '#6b7280', fontSize: 12 }} />
        <YAxis domain={[0, 1]} tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} tick={{ fill: '#6b7280', fontSize: 12 }} />
        <Tooltip content={<ProportionalTooltip />} />
        {topics.map((topic, index) => (
          <Line
            key={topic}
            type="monotone"
            dataKey={topic}
            stroke={CHART_COLORS[index % CHART_COLORS.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

function VisualizationStackedArea({ data, topics }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis dataKey="period" tick={{ fill: '#6b7280', fontSize: 12 }} />
        <YAxis domain={[0, 1]} tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} tick={{ fill: '#6b7280', fontSize: 12 }} />
        <Tooltip content={<ProportionalTooltip />} />
        {topics.map((topic, index) => (
          <Area
            key={topic}
            type="monotone"
            dataKey={topic}
            stackId="1"
            stroke={CHART_COLORS[index % CHART_COLORS.length]}
            fill={CHART_COLORS[index % CHART_COLORS.length]}
            fillOpacity={0.35}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}

function TopicHeatmap({ data, topics }) {
  if (!topics.length) return <p className="text-sm text-gray-500">No topics available for heatmap.</p>

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-gray-500">
            <th className="px-3 py-2">Period</th>
            {topics.map((topic) => (
              <th
                key={topic}
                className="px-3 py-2"
              >
                {topic}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.period}>
              <td className="px-3 py-2 font-medium text-gray-900">{row.period}</td>
              {topics.map((topic, idx) => {
                const value = row[topic] ?? 0
                const intensity = Math.max(0.05, Math.min(1, value))
                const bg = `rgba(37, 99, 235, ${0.1 + intensity * 0.6})`
                return (
                  <td
                    key={`${row.period}-${topic}`}
                    className="px-3 py-2 text-center text-xs font-semibold text-gray-900 rounded"
                    style={{ backgroundColor: bg }}
                  >
                    {(value * 100).toFixed(1)}%
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function VisualizationLocationCard({ visualizationPath, libraryPath }) {
  return (
    <Card className="border-gray-200 rounded-3xl shadow-sm">
      <CardHeader>
        <CardTitle className="text-2xl text-gray-900">Artifacts saved to disk</CardTitle>
        <p className="text-sm text-gray-500">
          Open the generated files directly in your vault or file explorer.
        </p>
      </CardHeader>
      <CardContent className="space-y-4 text-sm text-gray-700">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Visualization</p>
          <p className="mt-1 text-sm text-gray-500">{stripRoot(visualizationPath)}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Library path</p>
          {libraryPath ? (
            <p className="mt-1 text-sm text-gray-500">{stripRoot(libraryPath)}</p>
          ) : (
            <p className="mt-1 text-gray-500">
              Temporary library used. Rerun with “Save as permanent library” to persist it.
            </p>
          )}
          {/* Removed the permanent/temporary badge per request */}
        </div>
      </CardContent>
    </Card>
  )
}

function stripRoot(fullPath) {
  if (!fullPath) return ''
  const normalized = fullPath.replace(/\\/g, '/')
  const segments = normalized.split('/')
  if (segments.length < 2) return normalized
  return segments.slice(-2).join('/')
}

function ProportionalTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const sorted = [...payload]
    .filter((entry) => entry && typeof entry.value === 'number')
    .sort((a, b) => (b.value || 0) - (a.value || 0))

  return (
    <div className="rounded-2xl border border-gray-200 bg-white px-4 py-3 shadow-lg">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</p>
      <ul className="mt-2 space-y-1 text-sm">
        {sorted.map((entry) => (
          <li key={entry.dataKey} className="flex items-center gap-2 text-gray-700">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="flex-1 truncate">{entry.dataKey}</span>
            <span className="font-semibold">{((entry.value || 0) * 100).toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function buildTimeSpan(periodLabels) {
  if (!periodLabels || !periodLabels.length) return '—'
  const parseYear = (label) => {
    const match = label.match(/\d{4}/g)
    if (!match || !match.length) return null
    return Number(match[0])
  }
  const startYear = parseYear(periodLabels[0])
  const endYear = parseYear(periodLabels[periodLabels.length - 1])
  if (startYear && endYear) return `${startYear}-${endYear}`
  if (startYear) return `${startYear}`
  return periodLabels[0]
}
function PeriodCountsCard({ periods }) {
  if (!periods?.length) return null
  return (
    <Card className="border-gray-200 rounded-3xl shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-2xl text-gray-900">Period counts</CardTitle>
        <p className="text-sm text-gray-500">How many papers fall into each time period.</p>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 pt-2">
        {periods.map((period) => (
          <div
            key={period.period_label}
            className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm"
          >
            <p className="text-sm font-semibold text-gray-900">{period.period_label}</p>
            <p className="mt-2 text-3xl font-bold text-gray-900">{period.paper_count}</p>
            <p className="text-xs uppercase tracking-wide text-gray-500">papers</p>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
