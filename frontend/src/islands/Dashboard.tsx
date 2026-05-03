import React, { useCallback, useEffect, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import { api } from '../lib/api';
import type { WeatherSnapshot, TrafficIncident, Report } from '../lib/api';
import { getLang, t, type Lang } from '../i18n/index';
import KPIRow from './KPIRow';
import AIAnalysisCard from './AIAnalysisCard';
import WeatherCard from './WeatherCard';
import IncidentMap from './IncidentMap';
import CorrelationChart from './CorrelationChart';
import IncidentsTable from './IncidentsTable';

export default function Dashboard() {
  const [lang, setLangState] = useState<Lang>(() => getLang());
  const [weather, setWeather] = useState<WeatherSnapshot | null>(null);
  const [incidents, setIncidents] = useState<TrafficIncident[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    const handler = (e: Event) => setLangState((e as CustomEvent<Lang>).detail);
    window.addEventListener('wt-lang', handler);
    return () => window.removeEventListener('wt-lang', handler);
  }, []);

  useEffect(() => {
    async function load() {
      setDataLoading(true);
      setFetchError(null);
      try {
        const [w, inc] = await Promise.allSettled([
          api.weather.current(),
          api.traffic.incidents(),
        ]);
        if (w.status === 'fulfilled') setWeather(w.value);
        if (inc.status === 'fulfilled') setIncidents(inc.value);
        if (w.status === 'rejected' && inc.status === 'rejected') {
          setFetchError(t('en', 'error.fetch'));
        }
      } finally {
        setDataLoading(false);
      }
      try {
        setReport(await api.agent.latestReport());
      } catch {
        // No cached report yet — that is fine
      }
    }
    load();
  }, []);

  const handleGenerateReport = useCallback(async () => {
    setReportLoading(true);
    try {
      setReport(await api.agent.generateReport(lang));
    } catch (err) {
      console.error('Report generation failed:', err);
    } finally {
      setReportLoading(false);
    }
  }, [lang]);

  if (dataLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center gap-2 text-brand-mid">
        <svg
          className="h-5 w-5 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
        <span className="text-sm">{t(lang, 'loading')}</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-page">
      {/* Page header */}
      <div className="border-b border-brand-border bg-white px-6 py-5">
        <div className="mx-auto flex max-w-7xl items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-brand-slate">{t(lang, 'page.title')}</h1>
            <p className="mt-0.5 text-sm text-brand-mid">{t(lang, 'page.subtitle')}</p>
          </div>
          <button
            onClick={handleGenerateReport}
            disabled={reportLoading}
            className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-brand-orange px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-orange-dark disabled:cursor-not-allowed disabled:opacity-60"
          >
            {reportLoading ? t(lang, 'nav.generating') : t(lang, 'nav.generate')}
          </button>
        </div>
      </div>

      <div className="mx-auto max-w-7xl space-y-5 px-6 py-6">
        {fetchError && (
          <div className="rounded-card border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {fetchError}
          </div>
        )}

        <KPIRow lang={lang} weather={weather} incidents={incidents} />

        <AIAnalysisCard
          lang={lang}
          report={report}
          loading={reportLoading}
          onRegenerate={handleGenerateReport}
        />

        <div className="grid grid-cols-3 gap-5">
          <WeatherCard lang={lang} weather={weather} />
          <div className="col-span-2">
            <IncidentMap lang={lang} incidents={incidents} />
          </div>
        </div>

        <CorrelationChart lang={lang} />

        <IncidentsTable lang={lang} incidents={incidents} />

        <footer className="border-t border-brand-border pb-2 pt-4 text-center text-xs text-brand-mid">
          {t(lang, 'footer.attribution')}
        </footer>
      </div>
    </div>
  );
}
