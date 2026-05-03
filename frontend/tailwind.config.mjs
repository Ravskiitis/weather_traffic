/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'brand-orange': '#E85D2C',
        'brand-orange-dark': '#C94E22',
        'brand-slate': '#0F172A',
        'brand-mid': '#475569',
        'brand-light': '#EEF0F4',
        'brand-border': '#E2E5EB',
        'brand-page': '#F8F9FB',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '10px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-md': '0 4px 12px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
};
