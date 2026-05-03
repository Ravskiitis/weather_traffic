import React from 'react';
import { t, type Lang, type I18nKey } from '../i18n/index';
import type { TrafficIncident, IncidentSeverity, IncidentStatus, IncidentType } from '../lib/api';

interface Props {
  lang: Lang;
  incidents: TrafficIncident[];
}

const SEVERITY_STYLES: Record<IncidentSeverity, string> = {
  high: 'bg-red-100 text-red-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-emerald-100 text-emerald-700',
};

const SEVERITY_KEYS: Record<IncidentSeverity, I18nKey> = {
  high: 'severity.high',
  medium: 'severity.medium',
  low: 'severity.low',
};

const STATUS_STYLES: Record<IncidentStatus, string> = {
  active: 'bg-brand-orange/10 text-brand-orange',
  monitoring: 'bg-blue-100 text-blue-700',
  closed: 'bg-brand-light text-brand-mid',
};

const STATUS_KEYS: Record<IncidentStatus, I18nKey> = {
  active: 'status.active',
  monitoring: 'status.monitoring',
  closed: 'status.closed',
};

const TYPE_KEYS: Record<IncidentType, I18nKey> = {
  accident: 'type.accident',
  tunnel_closure: 'type.tunnel_closure',
  roadworks: 'type.roadworks',
  wind_warning: 'type.wind_warning',
  other: 'type.other',
};

function SeverityBadge({ s, lang }: { s: IncidentSeverity; lang: Lang }) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${SEVERITY_STYLES[s]}`}>
      {t(lang, SEVERITY_KEYS[s])}
    </span>
  );
}

function StatusBadge({ s, lang }: { s: IncidentStatus; lang: Lang }) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[s]}`}>
      {t(lang, STATUS_KEYS[s])}
    </span>
  );
}

export default function IncidentsTable({ lang, incidents }: Props) {
  const visible = incidents.filter((i) => i.status !== 'closed');
  const locale = lang === 'no' ? 'nb-NO' : 'en-GB';
  const dateFmt = new Intl.DateTimeFormat(locale, { dateStyle: 'short', timeStyle: 'short' });

  return (
    <div className="rounded-card bg-white shadow-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-brand-border px-5 py-4">
        <h3 className="text-sm font-semibold text-brand-slate">{t(lang, 'table.title')}</h3>
        <span className="text-xs text-brand-mid">{visible.length}</span>
      </div>

      {visible.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-brand-mid">
          {t(lang, 'table.noIncidents')}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-brand-border bg-brand-page text-xs text-brand-mid">
                <th className="px-5 py-2.5 text-left font-medium">{t(lang, 'table.type')}</th>
                <th className="px-5 py-2.5 text-left font-medium">{t(lang, 'table.location')}</th>
                <th className="px-5 py-2.5 text-left font-medium">{t(lang, 'table.road')}</th>
                <th className="px-5 py-2.5 text-left font-medium">{t(lang, 'table.severity')}</th>
                <th className="px-5 py-2.5 text-left font-medium">{t(lang, 'table.status')}</th>
                <th className="px-5 py-2.5 text-left font-medium">{t(lang, 'table.started')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border">
              {visible.map((inc) => (
                <tr key={inc.external_id} className="transition-colors hover:bg-brand-page/50">
                  <td className="px-5 py-3 text-xs">
                    {t(lang, TYPE_KEYS[inc.incident_type])}
                    {inc.source === 'demo_seed' && (
                      <span className="ml-1.5 inline-block rounded bg-brand-light px-1.5 py-0.5 text-[10px] font-medium text-brand-mid">
                        {t(lang, 'table.demo')}
                      </span>
                    )}
                  </td>
                  <td
                    className="max-w-[200px] truncate px-5 py-3 font-medium text-brand-slate"
                    title={inc.location_name}
                  >
                    {inc.location_name}
                  </td>
                  <td className="px-5 py-3 text-brand-mid">{inc.road_ref ?? '—'}</td>
                  <td className="px-5 py-3">
                    <SeverityBadge s={inc.severity} lang={lang} />
                  </td>
                  <td className="px-5 py-3">
                    <StatusBadge s={inc.status} lang={lang} />
                  </td>
                  <td className="whitespace-nowrap px-5 py-3 text-brand-mid">
                    {dateFmt.format(new Date(inc.started_at))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
