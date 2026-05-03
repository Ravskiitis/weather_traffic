import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { t, type Lang } from '../i18n/index';
import type { TrafficIncident, IncidentSeverity } from '../lib/api';

interface Props {
  lang: Lang;
  incidents: TrafficIncident[];
}

const BERGEN_CENTER: [number, number] = [60.39, 5.32];
const ZOOM = 10;

const SEVERITY_COLORS: Record<IncidentSeverity, string> = {
  high: '#E85D2C',
  medium: '#F59E0B',
  low: '#10B981',
};

function makeIcon(severity: IncidentSeverity): L.DivIcon {
  const color = SEVERITY_COLORS[severity];
  return L.divIcon({
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.3)"></div>`,
    className: '',
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -10],
  });
}

export default function IncidentMap({ lang, incidents }: Props) {
  const mapped = useMemo(
    () =>
      incidents.filter(
        (i) => i.latitude != null && i.longitude != null && i.status !== 'closed',
      ),
    [incidents],
  );

  return (
    <div className="flex h-full min-h-[360px] flex-col overflow-hidden rounded-card bg-white shadow-card">
      <div className="flex items-center justify-between border-b border-brand-border px-5 py-3">
        <h3 className="text-sm font-semibold text-brand-slate">{t(lang, 'map.title')}</h3>
        <span className="text-xs text-brand-mid">
          {mapped.length} {t(lang, 'map.incidents')}
        </span>
      </div>

      <div className="flex-1">
        <MapContainer
          center={BERGEN_CENTER}
          zoom={ZOOM}
          style={{ height: '100%', width: '100%', minHeight: 316 }}
          scrollWheelZoom={false}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          {mapped.map((inc) => (
            <Marker
              key={inc.external_id}
              position={[inc.latitude!, inc.longitude!]}
              icon={makeIcon(inc.severity)}
            >
              <Popup>
                <div style={{ fontSize: 12, lineHeight: 1.4 }}>
                  <p style={{ fontWeight: 600, marginBottom: 2 }}>{inc.location_name}</p>
                  {inc.road_ref && <p style={{ color: '#475569' }}>{inc.road_ref}</p>}
                  <p style={{ marginTop: 4 }}>{inc.incident_type.replace('_', ' ')}</p>
                  {inc.description && (
                    <p style={{ color: '#475569', marginTop: 4 }}>{inc.description}</p>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
