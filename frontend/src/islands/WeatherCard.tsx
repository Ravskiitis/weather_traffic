import React from 'react';
import { t, type Lang } from '../i18n/index';
import type { WeatherSnapshot } from '../lib/api';

interface Props {
  lang: Lang;
  weather: WeatherSnapshot | null;
}

function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-brand-border py-2 last:border-0">
      <span className="text-xs text-brand-mid">{label}</span>
      <span className="text-sm font-medium text-brand-slate">{value}</span>
    </div>
  );
}

function compassDir(deg: number): string {
  const dirs: string[] = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  return dirs[Math.round(deg / 45) % 8] ?? 'N';
}

export default function WeatherCard({ lang, weather }: Props) {
  if (!weather) {
    return (
      <div className="flex min-h-[180px] items-center justify-center rounded-card bg-white shadow-card">
        <p className="text-sm text-brand-mid">{t(lang, 'weather.none')}</p>
      </div>
    );
  }

  const fmt = (n: number | null | undefined, suffix: string) =>
    n != null ? `${n.toFixed(1)}${suffix}` : '—';

  const windStr = [
    fmt(weather.wind_speed_ms, ' m/s'),
    weather.wind_direction_deg != null ? compassDir(weather.wind_direction_deg) : null,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="rounded-card bg-white shadow-card p-5">
      <h3 className="mb-3 text-sm font-semibold text-brand-slate">{t(lang, 'weather.title')}</h3>

      <div className="mb-3 flex items-end gap-2">
        <span className="text-4xl font-bold tabular-nums text-brand-slate">
          {weather.temperature_c.toFixed(1)}
        </span>
        <span className="mb-1 text-xl text-brand-mid">°C</span>
        {weather.feels_like_c != null && (
          <span className="mb-1 ml-1 text-xs text-brand-mid">
            {t(lang, 'weather.feelsLike')} {weather.feels_like_c.toFixed(1)}°
          </span>
        )}
      </div>

      <p className="mb-3 text-xs text-brand-mid">{weather.location_name}</p>

      <DataRow label={t(lang, 'weather.wind')} value={windStr} />
      <DataRow label={t(lang, 'weather.humidity')} value={fmt(weather.humidity_pct, '%')} />
      <DataRow label={t(lang, 'weather.pressure')} value={fmt(weather.pressure_hpa, ' hPa')} />
      <DataRow label={t(lang, 'weather.source')} value={weather.source} />
    </div>
  );
}
