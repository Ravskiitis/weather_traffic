import React from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { t, type Lang } from '../i18n/index';
import { mockCorrelation } from '../data/mock-correlation';

interface Props {
  lang: Lang;
}

export default function CorrelationChart({ lang }: Props) {
  return (
    <div className="rounded-card bg-white shadow-card p-5">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-brand-slate">{t(lang, 'chart.title')}</h3>
        <p className="text-xs text-brand-mid">{t(lang, 'chart.subtitle')}</p>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={mockCorrelation} margin={{ top: 4, right: 36, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E5EB" vertical={false} />
          <XAxis
            dataKey="day"
            tick={{ fontSize: 12, fill: '#475569' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            yAxisId="left"
            tick={{ fontSize: 12, fill: '#475569' }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 12, fill: '#475569' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ borderRadius: 8, border: '1px solid #E2E5EB', fontSize: 12 }}
            labelStyle={{ fontWeight: 600 }}
          />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
          <Bar
            yAxisId="left"
            dataKey="incidents"
            name={t(lang, 'chart.incidents')}
            fill="#E85D2C"
            opacity={0.85}
            radius={[4, 4, 0, 0]}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="wind_ms"
            name={t(lang, 'chart.wind')}
            stroke="#0F172A"
            strokeWidth={2}
            dot={false}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="rain_mm"
            name={t(lang, 'chart.rain')}
            stroke="#475569"
            strokeWidth={1.5}
            strokeDasharray="4 2"
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
