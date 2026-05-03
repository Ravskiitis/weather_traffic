import React from 'react';
import { Sparkles, RefreshCw, Download, Share2 } from 'lucide-react';
import { t, type Lang, type I18nKey } from '../i18n/index';
import type { Report, ReportSection } from '../lib/api';

interface Props {
  lang: Lang;
  report: Report | null;
  loading: boolean;
  onRegenerate: () => void;
}

const SECTION_KEYS: Record<string, I18nKey> = {
  situation: 'report.section.situation',
  impact: 'report.section.impact',
  recommendations: 'report.section.recommendations',
  outlook: 'report.section.outlook',
};

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const [bg, fg] =
    value >= 0.85
      ? ['bg-emerald-100', 'text-emerald-700']
      : value >= 0.6
        ? ['bg-amber-100', 'text-amber-700']
        : ['bg-red-100', 'text-red-700'];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${bg} ${fg}`}>
      {pct}%
    </span>
  );
}

function Section({ section, lang }: { section: ReportSection; lang: Lang }) {
  return (
    <div>
      <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-brand-mid">
        {t(lang, SECTION_KEYS[section.title] ?? (section.title as I18nKey))}
      </h4>
      <p className="whitespace-pre-line text-sm leading-relaxed text-brand-slate">
        {section.content}
      </p>
    </div>
  );
}

export default function AIAnalysisCard({ lang, report, loading, onRegenerate }: Props) {
  const locale = lang === 'no' ? 'nb-NO' : 'en-GB';
  const formattedDate = report
    ? new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(
        new Date(report.generated_at),
      )
    : null;

  return (
    <div className="overflow-hidden rounded-card border-l-4 border-brand-orange bg-white shadow-card-md">
      {/* Header */}
      <div className="px-6 pt-5">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-orange/10 text-brand-orange">
              <Sparkles size={16} strokeWidth={2} />
            </span>
            <div>
              <h2 className="text-base font-semibold text-brand-slate">{t(lang, 'report.title')}</h2>
              <p className="text-xs text-brand-mid">{t(lang, 'report.poweredBy')}</p>
            </div>
          </div>
          {report && (
            <div className="flex items-center gap-3 text-xs text-brand-mid">
              {formattedDate && (
                <span>
                  {t(lang, 'report.generated')}: {formattedDate}
                </span>
              )}
              <ConfidenceBadge value={report.confidence} />
            </div>
          )}
        </div>

        {/* Body */}
        {loading && (
          <div className="flex items-center justify-center gap-3 py-10 text-brand-mid">
            <RefreshCw size={18} className="animate-spin" />
            <span className="text-sm">{t(lang, 'report.generating')}</span>
          </div>
        )}

        {!loading && !report && (
          <p className="py-8 text-center text-sm text-brand-mid">{t(lang, 'report.none')}</p>
        )}

        {!loading && report && (
          <div className="pb-5">
            <p className="mb-4 text-sm font-semibold leading-relaxed text-brand-slate">
              {report.summary}
            </p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {report.sections.map((s) => (
                <Section key={s.title} section={s} lang={lang} />
              ))}
            </div>
            {report.sources.length > 0 && (
              <div className="mt-4 border-t border-brand-border pt-3">
                <p className="text-xs text-brand-mid">
                  <span className="font-medium">{t(lang, 'report.sources')}:</span>{' '}
                  {report.sources.join(' · ')}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer actions */}
      <div className="flex items-center gap-2 border-t border-brand-border bg-brand-page px-6 py-3">
        <button
          onClick={onRegenerate}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-md bg-brand-orange px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-brand-orange-dark disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCw size={12} />
          {t(lang, 'report.regenerate')}
        </button>
        <button className="inline-flex items-center gap-1.5 rounded-md border border-brand-border px-3 py-1.5 text-xs font-medium text-brand-mid transition-colors hover:border-brand-slate hover:text-brand-slate">
          <Download size={12} />
          {t(lang, 'report.export')}
        </button>
        <button className="inline-flex items-center gap-1.5 rounded-md border border-brand-border px-3 py-1.5 text-xs font-medium text-brand-mid transition-colors hover:border-brand-slate hover:text-brand-slate">
          <Share2 size={12} />
          {t(lang, 'report.share')}
        </button>
      </div>
    </div>
  );
}
