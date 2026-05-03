/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}',
  ],
  theme: {
    extend: {
      // Design tokens will be extracted from docs/design/raw/prototype.html
      // and populated here during the Claude Design handoff step.
    },
  },
  plugins: [],
};
