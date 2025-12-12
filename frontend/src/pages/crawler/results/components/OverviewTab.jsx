import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'

export default function OverviewTab({ networkOverview, circleMetrics, temporalData }) {
  return (
    <>
      <section className="bg-white rounded-3xl border border-gray-200 shadow-sm p-6 space-y-6">
        <h2 className="text-2xl font-semibold text-gray-900">Network overview</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {networkOverview.map((item) => (
            <div
              key={item.label}
              className="rounded-3xl border border-gray-100 bg-gray-50 p-6 shadow-sm"
            >
              <p className="text-[11px] uppercase tracking-[0.3em] text-gray-500">{item.label}</p>
              <p className="mt-2 text-3xl font-semibold text-gray-900">{item.value}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white rounded-3xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Network detail metrics</h2>
        <div className="flex flex-col items-center gap-6 md:flex-row md:justify-around">
          {circleMetrics.map((metric) => (
            <div key={metric.label} className="text-center">
              <div className="w-40 h-40 rounded-full border-4 border-gray-200 flex items-center justify-center text-4xl font-bold text-gray-900 shadow-inner bg-white">
                {metric.value}
              </div>
              <p className="mt-3 text-sm font-medium text-gray-600">{metric.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white rounded-3xl border border-gray-200 shadow-sm p-6 space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900">Temporal distribution</h2>
        {temporalData.length ? (
          <div className="w-full h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={temporalData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="year" tick={{ fill: '#6b7280', fontSize: 12 }} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="paper_count" fill="#cbd5f5" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="text-sm text-gray-500">No temporal data available yet.</p>
        )}
      </section>
    </>
  )
}
