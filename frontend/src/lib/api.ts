/**
 * Typed fetch helpers for the weather_traffic backend API.
 *
 * Usage in Astro components (server-side):
 *   const weather = await api.weather.current();
 *
 * Usage in React islands (client-side):
 *   const weather = await api.weather.current();
 *
 * import.meta.env.PUBLIC_BACKEND_URL is set in .env (Astro exposes PUBLIC_* vars
 * to both SSR and client bundles via Vite).
 */

const BASE_URL =
  (import.meta.env.PUBLIC_BACKEND_URL as string | undefined) ?? 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Types — mirror the backend pydantic schemas
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  version: string;
}

export interface WeatherSnapshot {
  id: number | null;
  timestamp: string;            // ISO 8601, naive UTC
  location_name: string;
  latitude: number;
  longitude: number;
  temperature_c: number;
  feels_like_c: number | null;
  wind_speed_ms: number;
  wind_direction_deg: number | null;
  humidity_pct: number | null;
  pressure_hpa: number | null;
  precipitation_mm_h: number | null;
  weather_symbol: string | null; // MET Norway symbol code, e.g. "heavyrain"
  source: string;
  fetched_at: string;
}

export type IncidentSeverity = 'low' | 'medium' | 'high';
export type IncidentStatus = 'scheduled' | 'active' | 'monitoring' | 'closed';
export type IncidentType = 'accident' | 'tunnel_closure' | 'roadworks' | 'wind_warning' | 'other';

export interface TrafficIncident {
  id: number | null;
  external_id: string;
  source: string;
  incident_type: IncidentType;
  location_name: string;
  road_ref: string | null;
  latitude: number | null;
  longitude: number | null;
  severity: IncidentSeverity;
  started_at: string;
  ended_at: string | null;
  description: string | null;
  status: IncidentStatus;
  fetched_at: string;
}

export interface ReportSection {
  title: 'situation' | 'impact' | 'recommendations' | 'outlook';
  content: string;
}

export interface Report {
  generated_at: string;
  model: string;
  confidence: number;           // 0.0 – 1.0
  language: 'no' | 'en';
  summary: string;
  sections: ReportSection[];
  sources: string[];
  referenced_entities: string[];
}

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly path: string,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ---------------------------------------------------------------------------
// Base fetch helper
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, init);

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json() as { detail?: string; error?: string };
      detail = body.detail ?? body.error ?? detail;
    } catch {
      // ignore JSON parse errors on error responses
    }
    throw new ApiError(response.status, path, `${response.status} ${detail}`);
  }

  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// API surface
// ---------------------------------------------------------------------------

export const api = {
  health: () =>
    apiFetch<HealthResponse>('/api/health'),

  weather: {
    current: () =>
      apiFetch<WeatherSnapshot>('/api/weather/current'),
  },

  traffic: {
    incidents: () =>
      apiFetch<TrafficIncident[]>('/api/traffic/incidents'),

    refresh: () =>
      apiFetch<{ upserted: number }>('/api/traffic/refresh', { method: 'POST' }),
  },

  agent: {
    generateReport: (language: 'en' | 'no' = 'en') =>
      apiFetch<Report>(`/api/agent/report?language=${language}`, { method: 'POST' }),

    latestReport: () =>
      apiFetch<Report>('/api/agent/report/latest'),
  },
} as const;
