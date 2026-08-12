"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import ChatPanel from "@/components/ChatPanel";

const SatelliteMap = dynamic(() => import("@/components/SatelliteMap"), { ssr: false });

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

interface Insight {
  event_id: string;
  title: string;
  brief: string;
  imagery_url: string;
  hotspot_count: number;
  analysis: {
    estimated_area_ha: number;
    total_frp_mw: number;
    risk_level: string;
    hotspot_count: number;
  };
  categories: string[];
}

interface Event {
  id: string;
  title: string;
  geometry: { date: string; coordinates: [number, number] }[];
}

const RISK_COLORS: Record<string, string> = {
  low: "bg-green-800 text-green-200",
  medium: "bg-yellow-800 text-yellow-200",
  high: "bg-orange-800 text-orange-200",
  critical: "bg-red-800 text-red-200",
};

export default function EventDetailPage() {
  const params = useParams<{ id: string }>();
  const eventId = params?.id ?? "";

  const [event, setEvent] = useState<Event | null>(null);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  // Fetch event metadata
  useEffect(() => {
    if (!eventId) return;
    fetch(`${API}/events/${eventId}`)
      .then((r) => r.json())
      .then(setEvent)
      .catch(() => setError("Event not found."));
  }, [eventId]);

  // Auto-generate insight on load
  useEffect(() => {
    if (!eventId) return;
    setGenerating(true);
    fetch(`${API}/insights/${eventId}`, { method: "POST" })
      .then((r) => r.json())
      .then(setInsight)
      .catch(() => setError("Failed to generate insight."))
      .finally(() => setGenerating(false));
  }, [eventId]);

  const coords = event?.geometry?.[event.geometry.length - 1]?.coordinates;
  const lat = coords?.[1] ?? 0;
  const lon = coords?.[0] ?? 0;
  const risk = insight?.analysis?.risk_level ?? "low";

  return (
    <div className="space-y-6">
      {/* Back link */}
      <a href="/" className="text-blue-400 text-sm hover:underline">
        ← Back to Dashboard
      </a>

      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          {event?.title ?? "Loading event…"}
        </h1>
        {coords && (
          <p className="text-gray-400 text-sm mt-1">
            Lat {lat.toFixed(3)}, Lon {lon.toFixed(3)}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Map */}
        <div className="rounded-xl overflow-hidden border border-gray-800 h-80">
          {coords && <SatelliteMap lat={lat} lon={lon} imageryUrl={insight?.imagery_url ?? ""} />}
        </div>

        {/* Brief */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-white">Situation Brief</h2>
            {risk && (
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${RISK_COLORS[risk] ?? ""}`}>
                {risk.toUpperCase()} RISK
              </span>
            )}
          </div>

          {generating && (
            <p className="text-gray-400 animate-pulse text-sm">
              Fetching imagery and generating brief via IBM Granite…
            </p>
          )}

          {error && <p className="text-red-400 text-sm">{error}</p>}

          {insight && !generating && (
            <>
              {insight.brief.startsWith("IBM Granite API key not configured") ||
               insight.brief.startsWith("[Granite offline") ? (
                <div className="flex items-start gap-2 text-sm text-amber-500/80 bg-amber-950/40 border border-amber-900/40 rounded-lg px-4 py-3">
                  <span className="mt-0.5">⚠</span>
                  <div>
                    <p className="font-medium">AI brief unavailable</p>
                    <p className="text-amber-600/70 text-xs mt-0.5">
                      Add <code className="font-mono">WATSONX_API_KEY</code> and{" "}
                      <code className="font-mono">WATSONX_PROJECT_ID</code> to your{" "}
                      <code className="font-mono">.env</code> file, then restart the backend.
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-gray-200 text-sm leading-relaxed">{insight.brief}</p>
              )}

              {/* Stats grid — always shown regardless of brief state */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                {[
                  { label: "Hotspots", value: insight.analysis?.hotspot_count ?? 0 },
                  { label: "Est. Area", value: `${insight.analysis?.estimated_area_ha ?? 0} ha` },
                  { label: "Fire Radiative Power", value: `${insight.analysis?.total_frp_mw ?? 0} MW` },
                  { label: "Category", value: insight.categories?.[0] ?? "N/A" },
                ].map((s) => (
                  <div key={s.label} className="bg-gray-800 rounded-lg p-3">
                    <p className="text-xs text-gray-500">{s.label}</p>
                    <p className="text-white font-semibold mt-0.5">{String(s.value)}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Satellite imagery */}
      {insight?.imagery_url && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-white">MODIS Satellite Tile</h2>
          <div className="rounded-xl overflow-hidden border border-gray-800 inline-block">
            <img
              src={insight.imagery_url}
              alt="GIBS satellite imagery tile"
              className="max-w-full"
              onError={(e) => (e.currentTarget.style.display = "none")}
            />
          </div>
          <p className="text-xs text-gray-500">Source: NASA GIBS WMTS</p>
        </div>
      )}

      {/* Chat panel */}
      <div className="border-t border-gray-800 pt-6">
        <h2 className="text-lg font-semibold text-white mb-4">Ask the Satellite Agent</h2>
        <ChatPanel eventId={eventId} />
      </div>
    </div>
  );
}
