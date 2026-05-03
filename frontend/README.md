# weather_traffic — Frontend

Astro 4.x dashboard for the Bergen weather/traffic B2B application.

## Quick start

```bash
# 1. Install dependencies (npm — no pnpm/yarn lockfile committed)
npm install

# 2. Set the backend URL (optional — defaults to http://localhost:8000)
echo 'PUBLIC_BACKEND_URL=http://localhost:8000' > .env

# 3. Start the dev server (http://localhost:4321)
npm run dev
```

The backend must be running on port 8000 for data to load. See `backend/README.md`.

## Scripts

| Command           | Description                        |
|-------------------|------------------------------------|
| `npm run dev`     | Dev server with HMR at port 4321   |
| `npm run build`   | Production build to `dist/`        |
| `npm run preview` | Preview production build locally   |
| `npm run check`   | TypeScript + Astro type checking   |

## Project layout

```
src/
├── pages/       Astro routes (index.astro = dashboard)
├── layouts/     Page shells
├── components/  Static Astro components
├── islands/     React islands (client:visible — charts, map, toggle)
├── lib/
│   └── api.ts   Typed fetch helpers for the backend
├── i18n/        en.json / no.json — all user-facing strings
└── styles/      Global Tailwind overrides (if needed)
public/          Static assets
```

## Design source of truth

Before touching any component, open `docs/design/raw/prototype.html` in a browser.
Design tokens (colors, radii, shadows, fonts) live in `tailwind.config.mjs`.

## Backend API endpoints consumed

- `GET  /api/health`
- `GET  /api/weather/current`
- `GET  /api/traffic/incidents`
- `POST /api/traffic/refresh`
- `POST /api/agent/report?language=en|no`
- `GET  /api/agent/report/latest`
