export interface CorrelationPoint {
  day: string;
  incidents: number;
  wind_ms: number;
  rain_mm: number;
}

export const mockCorrelation: CorrelationPoint[] = [
  { day: 'Mon', incidents: 3, wind_ms: 8.2, rain_mm: 1.4 },
  { day: 'Tue', incidents: 5, wind_ms: 12.4, rain_mm: 4.8 },
  { day: 'Wed', incidents: 8, wind_ms: 18.6, rain_mm: 12.2 },
  { day: 'Thu', incidents: 4, wind_ms: 11.1, rain_mm: 3.6 },
  { day: 'Fri', incidents: 2, wind_ms: 6.8, rain_mm: 0.2 },
  { day: 'Sat', incidents: 1, wind_ms: 5.2, rain_mm: 0.0 },
  { day: 'Sun', incidents: 6, wind_ms: 16.4, rain_mm: 8.7 },
];
