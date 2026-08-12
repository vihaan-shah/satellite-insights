"use client";

import { useEffect, useRef } from "react";

interface Props {
  lat: number;
  lon: number;
  imageryUrl?: string;
}

export default function SatelliteMap({ lat, lon }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapInstanceRef = useRef<any>(null);

  useEffect(() => {
    if (!mapRef.current) return;

    // Guard: if Leaflet has already stamped this container, bail out
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if ((mapRef.current as any)._leaflet_id) return;

    // Cancel flag — prevents the async callback from running after cleanup
    let cancelled = false;

    import("leaflet").then((L) => {
      if (cancelled || !mapRef.current) return;

      // Guard again inside async callback (Strict Mode double-invoke)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if ((mapRef.current as any)._leaflet_id) return;

      // Fix default marker icon paths for Next.js
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const map = L.map(mapRef.current, { preferCanvas: true }).setView([lat, lon], 7);
      mapInstanceRef.current = map;

      // Base layer: OpenStreetMap
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
        maxZoom: 18,
      }).addTo(map);

      // GIBS MODIS True Color overlay
      L.tileLayer(
        "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2024-07-01/GoogleMapsCompatible/{z}/{y}/{x}.jpg",
        {
          attribution: "NASA GIBS",
          opacity: 0.7,
          maxZoom: 9,
          errorTileUrl: "",
        }
      ).addTo(map);

      // Event marker
      L.marker([lat, lon])
        .addTo(map)
        .bindPopup(`<b>Event Location</b><br>Lat: ${lat.toFixed(3)}, Lon: ${lon.toFixed(3)}`)
        .openPopup();
    });

    return () => {
      cancelled = true;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // run once on mount — lat/lon are set at mount time

  return (
    <>
      {/* Leaflet CSS */}
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      />
      <div ref={mapRef} className="w-full h-full" />
    </>
  );
}
