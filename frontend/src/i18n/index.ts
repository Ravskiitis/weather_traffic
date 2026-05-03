import en from './en.json';
import no from './no.json';

export type Lang = 'en' | 'no';
export type I18nKey = keyof typeof en;

const bundles: Record<Lang, Record<string, string>> = { en, no };

export function t(lang: Lang, key: I18nKey): string {
  return bundles[lang]?.[key] ?? bundles.en[key] ?? key;
}

export function getLang(): Lang {
  if (typeof window === 'undefined') return 'en';
  return (localStorage.getItem('wt-lang') as Lang) ?? 'en';
}

export function setLang(lang: Lang): void {
  localStorage.setItem('wt-lang', lang);
  window.dispatchEvent(new CustomEvent<Lang>('wt-lang', { detail: lang }));
}
