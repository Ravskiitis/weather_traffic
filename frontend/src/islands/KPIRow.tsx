import React from 'react';
import { t, type Lang } from '../i18n/index';
import type { WeatherSnapshot, TrafficIncident } from '../lib/api';

interface Props {
  lang: Lang;
  weather: WeatherSnapshot | null;
  incidents: TrafficIncident[];
}

function KPICard({
  label,
  value,
  unit,
  badge,
}: {
  label: string;
  value: string | number;
  unit?: string;
  badge?: { text: string; color: string };
}) {
  return (
    <div className="rounded-card bg-white shadow-card px-5 py-4">
      <p className="text-xs font-medium uppercase tracking-wide text-brand-mid">{label}</p>
      <div className="mt-1 flex items-end gap-1.5">
        <span className="text-3xl font-bold tabular-nums text-brand-slate">{value}</span>
        {unit && <span className="mb-0.5 text-sm text-brand-mid">{unit}</span>}
      </div>
      {badge && (
        <span
          className={`mt-1.5 inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${badge.color}`}
        >
          {badge.text}
        </span>
      )}
    </div>
  );
}

export default function KPIRow({ lang, weather, incidents }: Props) {
  const active = incidents.filter((i) => i.status === 'active').length;
  const tunnelsClosed = incidents.filter(
    (i) => i.incident_type === 'tunnel_closure' && i.status === 'active',
  ).length;
  const temp = weather?.temperature_c;
  const rain = weather?.precipitation_mm_h ?? 0;

  const activeBadge =
    active >= 5
      ? { text: '↑ High', color: 'bg-red-100 text-red-700' }
      : active >= 2
        ? { text: '→ Normal', color: 'bg-amber-100 text-amber-700' }
        : { text: '↓ Low', color: 'bg-emerald-100 text-emerald-700' };

  const rainBadge =
    rain > 5
      ? { text: t(lang, 'kpi.risk.high'), color: 'bg-red-100 text-red-700' }
      : rain > 1
        ? { text: t(lang, 'kpi.risk.moderate'), color: 'bg-amber-100 text-amber-700' }
        : { text: t(lang, 'kpi.risk.low'), color: 'bg-emerald-100 text-emerald-700' };

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <KPICard label={t(lang, 'kpi.activeIncidents')} value={active} badge={activeBadge} />
      <KPICard label={t(lang, 'kpi.closedTunnels')} value={tunnelsClosed} />
      <KPICard
        label={t(lang, 'kpi.temperature')}
        value={temp != null ? temp.toFixed(1) : '—'}
        unit="°C"
      />
      <KPICard
        label={t(lang, 'kpi.precipitation')}
        value={rain.toFixed(1)}
        unit="mm/h"
        badge={rainBadge}
      />
    </div>
  );
}
