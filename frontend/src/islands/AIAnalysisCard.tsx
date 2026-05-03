import React, { useState } from 'react';
import { Sparkles, RefreshCw, Download, Share2, ChevronDown, ChevronUp } from 'lucide-react';
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function extractListItems(text: string, max: number): string[] {
  const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);

  const numbered = lines
    .filter((l) => /^\d+[\.\)]/.test(l))
    .map((l) => l.replace(/^\d+[\.\)]\s*/, '').replace(/\.$/, '').trim());
  if (numbered.length >= 1) return numbered.slice(0, max);

  const bulleted = lines
    .filter((l) => /^[•\-\*·]/.test(l))
    .map((l) => l.replace(/^[•\-\*·]\s*/, '').replace(/\.$/, '').trim());
  if (bulleted.length >= 1) return bulleted.slice(0, max);

  return text
    .split(/\.\s+/)
    .map((s) => s.trim().replace(/\.$/, ''))
    .filter(Boolean)
    .slice(0, max);
}

function firstLine(text: string): string {
  return text.split('\n').map((l) => l.trim()).find(Boolean) ?? text.trim();
}

function sectionContent(sections: ReportSection[], title: string): string {
  return sections.find((s) => s.title === title)?.content ?? '';
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ConfidenceBadge({ value, lang }: { value: number; lang: Lang }) {
  const pct = Math.round(value * 100);
  const [bg, fg] =
    value >= 0.85
      ? ['bg-emerald-100', 'text-emerald-700']
      : value >= 0.6
        ? ['bg-amber-100', 'text-amber-700']
        : ['bg-red-100', 'text-red-700'];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${bg} ${fg}`}
      title={t(lang, 'report.confidence')}
    >
      {pct}%
    </span>
  );
}

function SectionDetail({ section, lang }: { section: ReportSection; lang: Lang }) {
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

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function AIAnalysisCard({ lang, report, loading, onRegenerate }: Props) {
  const [expanded, setExpanded] = useState(false);

  const locale = lang === 'no' ? 'nb-NO' : 'en-GB';
  const formattedDate = report
    ? new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(
        new Date(report.generated_at),
      )
    : null;

  const actions = report
    ? extractListItems(sectionContent(report.sections, 'recommendations'), 3)
    : [];
  const risks = report
    ? extractListItems(sectionContent(report.sections, 'impact'), 3)
    : [];
  const outlookLine = report ? firstLine(sectionContent(report.sections, 'outlook')) : '';

  return (
    <div id="wt-report-card" className="overflow-hidden rounded-card border-l-4 border-brand-orange bg-white shadow-card-md">

      {/* ── Print-only page header (hidden on screen) ── */}
      <div className="hidden print:block border-b border-gray-200 px-6 pt-6 pb-4">
        <p className="text-lg font-bold text-black">weather_traffic — AI Operational Report</p>
        {formattedDate && (
          <p className="mt-0.5 text-sm text-gray-500">
            {t(lang, 'report.generated')}: {formattedDate}
          </p>
        )}
      </div>

      {/* ── Screen header (hidden in print — replaced by print header above) ── */}
      <div className="print:hidden flex items-center justify-between gap-4 border-b border-brand-border px-6 py-4">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-brand-orange/10 text-brand-orange">
            <Sparkles size={14} strokeWidth={2} />
          </span>
          <span className="font-semibold text-brand-slate">{t(lang, 'report.title')}</span>
          <span className="text-brand-border">—</span>
          <span className="text-xs text-brand-mid">{t(lang, 'report.poweredBy')}</span>
        </div>
        <div className="flex items-center gap-3">
          {formattedDate && (
            <span className="hidden text-xs text-brand-mid sm:block">{formattedDate}</span>
          )}
          {report && <ConfidenceBadge value={report.confidence} lang={lang} />}
        </div>
      </div>

      {/* ── Body ── */}
      <div className="px-6 py-5">
        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center gap-3 py-10 text-brand-mid">
            <RefreshCw size={18} className="animate-spin" />
            <span className="text-sm">{t(lang, 'report.generating')}</span>
          </div>
        )}

        {/* Empty */}
        {!loading && !report && (
          <p className="py-8 text-center text-sm text-brand-mid">{t(lang, 'report.none')}</p>
        )}

        {/* Report content */}
        {!loading && report && (
          <div className="space-y-5">
            {/* Summary */}
            <p className="text-[15px] font-semibold leading-snug text-brand-slate">
              {report.summary}
            </p>

            {/* Top 3 Actions */}
            {actions.length > 0 && (
              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-mid">
                  {t(lang, 'report.actions')}
                </h4>
                <ol className="space-y-1.5">
                  {actions.map((action, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-brand-slate">
                      <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-orange text-[10px] font-bold text-white">
                        {i + 1}
                      </span>
                      {action}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* Key Risks */}
            {risks.length > 0 && (
              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-mid">
                  {t(lang, 'report.risks')}
                </h4>
                <ul className="space-y-1.5">
                  {risks.map((risk, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-brand-slate">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-orange" />
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Outlook */}
            {outlookLine && (
              <div className="rounded-md bg-brand-light px-3 py-2.5 text-sm text-brand-slate">
                <span className="mr-1 text-xs font-semibold uppercase tracking-wide text-brand-mid">
                  {t(lang, 'report.section.outlook')}:
                </span>
                {outlookLine}
              </div>
            )}

            {/* Toggle button — hidden in print (full sections always render in print via CSS) */}
            <button
              onClick={() => setExpanded((v) => !v)}
              className="print:hidden flex items-center gap-1 text-xs font-medium text-brand-mid transition-colors hover:text-brand-slate"
              aria-expanded={expanded}
            >
              {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              {t(lang, expanded ? 'report.hideFull' : 'report.showFull')}
            </button>

            {/*
             * Full 4-section detail.
             * On screen: toggled by `expanded` (grid vs hidden).
             * In print:  wt-full-sections CSS rule forces display:grid regardless.
             */}
            <div
              className={`wt-full-sections grid-cols-1 gap-4 border-t border-brand-border pt-4 sm:grid-cols-2 ${
                expanded ? 'grid' : 'hidden'
              }`}
            >
              {report.sections.map((s) => (
                <SectionDetail key={s.title} section={s} lang={lang} />
              ))}
            </div>

            {/* Sources — follow same collapsed/expanded state as sections */}
            {report.sources.length > 0 && (
              <div className={expanded ? 'border-t border-brand-border pt-3' : 'hidden print:block border-t border-brand-border pt-3'}>
                <p className="text-xs text-brand-mid">
                  <span className="font-medium">{t(lang, 'report.sources')}:</span>{' '}
                  {report.sources.join(' · ')}
                </p>
              </div>
            )}

            {/* Print-only footer (hidden on screen) */}
            <div className="hidden print:block border-t border-gray-200 pt-4 text-xs text-gray-500">
              Data: MET Norway · Statens vegvesen / NPRA · Generated by Claude Sonnet 4.6
            </div>
          </div>
        )}
      </div>

      {/* ── Footer actions (hidden in print) ── */}
      <div className="print:hidden flex items-center gap-2 border-t border-brand-border bg-brand-page px-6 py-3">
        <button
          onClick={onRegenerate}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-md bg-brand-orange px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-brand-orange-dark disabled:cursor-not-allowed disabled:opacity-60"
        >
          <RefreshCw size={12} />
          {t(lang, 'report.regenerate')}
        </button>
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-1.5 rounded-md border border-brand-border px-3 py-1.5 text-xs font-medium text-brand-mid transition-colors hover:border-brand-slate hover:text-brand-slate"
        >
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
