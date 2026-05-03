import React, { useEffect, useState } from 'react';
import { getLang, setLang, t, type Lang } from '../i18n/index';

export default function LanguageToggle() {
  const [lang, setLangState] = useState<Lang>('en');

  useEffect(() => {
    setLangState(getLang());
    const handler = (e: Event) => setLangState((e as CustomEvent<Lang>).detail);
    window.addEventListener('wt-lang', handler);
    return () => window.removeEventListener('wt-lang', handler);
  }, []);

  function toggle() {
    const next: Lang = lang === 'en' ? 'no' : 'en';
    setLang(next);
  }

  return (
    <button
      onClick={toggle}
      aria-label={`Switch to ${lang === 'en' ? 'Norwegian' : 'English'}`}
      className="inline-flex h-8 w-12 items-center justify-center rounded-md border border-brand-border text-xs font-semibold text-brand-mid transition-colors hover:border-brand-orange hover:text-brand-orange"
    >
      {t(lang, 'lang.switch')}
    </button>
  );
}
