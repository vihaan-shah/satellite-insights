"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

interface EventPoint {
  id: string;
  title: string;
  lat: number;
  lon: number;
  category: string;
  date: string;
}

// Category → marker colour (Leaflet divIcon)
const CAT_COLOR: Record<string, string> = {
  wildfires:    "#f97316",
  floods:       "#38bdf8",
  severeStorms: "#a78bfa",
  volcanoes:    "#f43f5e",
  default:      "#94a3b8",
};

const CAT_EMOJI: Record<string, string> = {
  wildfires:    "🔥",
  severeStorms: "⛈",
  floods:       "🌊",
  volcanoes:    "🌋",
  default:      "📍",
};

function markerIcon(L: typeof import("leaflet"), categoryId: string) {
  const color = CAT_COLOR[categoryId] ?? CAT_COLOR.default;
  const emoji = CAT_EMOJI[categoryId] ?? CAT_EMOJI.default;
  return L.divIcon({
    className: "",
    html: `
      <div style="
        width:32px;height:32px;border-radius:50% 50% 50% 0;
        background:${color};border:2px solid #fff;
        transform:rotate(-45deg);
        box-shadow:0 2px 8px rgba(0,0,0,0.5);
        display:flex;align-items:center;justify-content:center;
      ">
        <span style="transform:rotate(45deg);font-size:13px;line-height:1;">${emoji}</span>
      </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -34],
  });
}

export default function EventsMap({ events }: { events: EventPoint[] }) {
  const mapRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapInstanceRef = useRef<any>(null);
  const router = useRouter();

  useEffect(() => {
    if (!mapRef.current) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if ((mapRef.current as any)._leaflet_id) return;

    let cancelled = false;

    import("leaflet").then((L) => {
      if (cancelled || !mapRef.current) return;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if ((mapRef.current as any)._leaflet_id) return;

      const map = L.map(mapRef.current, {
        preferCanvas: true,
        zoomControl: true,
        scrollWheelZoom: true,
      }).setView([20, 0], 2);

      mapInstanceRef.current = map;

      // Dark base tile (CartoDB Dark Matter)
      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        {
          attribution: '© <a href="https://carto.com/">CARTO</a> © OpenStreetMap',
          subdomains: "abcd",
          maxZoom: 19,
        }
      ).addTo(map);

      // Add a marker per event
      events.forEach((ev) => {
        if (!ev.lat || !ev.lon) return;
        const icon = markerIcon(L, ev.category);
        const marker = L.marker([ev.lat, ev.lon], { icon });

        marker.bindPopup(`
          <div style="min-width:180px;font-family:system-ui,sans-serif;">
            <p style="font-weight:700;font-size:13px;margin:0 0 4px;color:#1f2328;">${ev.title}</p>
            <p style="font-size:11px;color:#57606a;margin:0 0 8px;">${ev.date}</p>
            <a href="/events/${ev.id}"
               style="display:inline-block;background:#3b82f6;color:#fff;font-size:11px;
                      padding:4px 10px;border-radius:6px;text-decoration:none;font-weight:600;">
              View Situation Brief →
            </a>
          </div>
        `);

        // Also navigate on marker click (popup opens first, link navigates)
        marker.on("click", () => {
          marker.openPopup();
        });

        marker.addTo(map);
      });

      // Fit bounds to all markers if we have any
      const validPoints = events.filter((e) => e.lat && e.lon);
      if (validPoints.length > 1) {
        const bounds = L.latLngBounds(validPoints.map((e) => [e.lat, e.lon]));
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 6 });
      }
    });

    return () => {
      cancelled = true;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // When events change after initial mount, add new markers without re-initialising
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || events.length === 0) return;

    import("leaflet").then((L) => {
      // Remove all existing markers first
      map.eachLayer((layer: unknown) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        if ((layer as any) instanceof L.Marker) map.removeLayer(layer as any);
      });

      events.forEach((ev) => {
        if (!ev.lat || !ev.lon) return;
        const icon = markerIcon(L, ev.category);
        const marker = L.marker([ev.lat, ev.lon], { icon });
        marker.bindPopup(`
          <div style="min-width:180px;font-family:system-ui,sans-serif;">
            <p style="font-weight:700;font-size:13px;margin:0 0 4px;color:#1f2328;">${ev.title}</p>
            <p style="font-size:11px;color:#57606a;margin:0 0 8px;">${ev.date}</p>
            <a href="/events/${ev.id}"
               style="display:inline-block;background:#3b82f6;color:#fff;font-size:11px;
                      padding:4px 10px;border-radius:6px;text-decoration:none;font-weight:600;">
              View Situation Brief →
            </a>
          </div>
        `);
        marker.addTo(map);
      });
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events]);

  return (
    <>
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <div ref={mapRef} className="w-full h-full" />
    </>
  );
}
