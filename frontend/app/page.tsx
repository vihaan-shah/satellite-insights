"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";

const EventsMap = dynamic(() => import("@/components/EventsMap"), { ssr: false });

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

interface Event {
  id: string;
  title: string;
  categories: { id: string; title: string }[];
  geometry: { date: string; coordinates: [number, number] }[];
  status: string;
}

const CATEGORY_FILTERS = [
  { id: "", label: "All Events" },
  { id: "wildfires", label: "🔥 Wildfires" },
  { id: "floods", label: "🌊 Floods" },
  { id: "severeStorms", label: "⛈ Storms" },
  { id: "volcanoes", label: "🌋 Volcanoes" },
];

const CAT_DOT: Record<string, string> = {
  wildfires:    "bg-orange-500",
  floods:       "bg-sky-400",
  severeStorms: "bg-violet-400",
  volcanoes:    "bg-rose-500",
};

export default function DashboardPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    const url = category
      ? `${API}/events?category=${category}&limit=50`
      : `${API}/events?limit=50`;

    fetch(url)
      .then((r) => r.json())
      .then((data) => setEvents(Array.isArray(data) ? data : []))
      .catch(() => setError("Failed to load events. Is the backend running?"))
      .finally(() => setLoading(false));
  }, [category]);

  // Convert events → map points
  const mapPoints = events
    .filter((ev) => ev.geometry?.length)
    .map((ev) => {
      const last = ev.geometry[ev.geometry.length - 1];
      return {
        id: ev.id,
        title: ev.title,
        lat: last.coordinates[1],
        lon: last.coordinates[0],
        category: ev.categories?.[0]?.id ?? "default",
        date: last.date?.slice(0, 10) ?? "",
      };
    });

  return (
    <div className="flex flex-col gap-6">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-end gap-4 justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Active Natural Events</h1>
          <p className="text-gray-400 mt-1 text-sm">
            Real-time data from NASA EONET · Click a marker or event card to generate an AI situation brief
          </p>
        </div>
        {/* Legend */}
        <div className="flex flex-wrap gap-3 text-xs text-gray-400">
          {[
            { id: "wildfires",    label: "Wildfire",  color: "bg-orange-500" },
            { id: "floods",       label: "Flood",     color: "bg-sky-400" },
            { id: "severeStorms", label: "Storm",     color: "bg-violet-400" },
            { id: "volcanoes",    label: "Volcano",   color: "bg-rose-500" },
          ].map((l) => (
            <span key={l.id} className="flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded-full ${l.color}`} />
              {l.label}
            </span>
          ))}
        </div>
      </div>

      {/* ── Full-width map ── */}
      <div className="w-full rounded-2xl overflow-hidden border border-gray-800" style={{ height: "480px" }}>
        {loading ? (
          <div className="w-full h-full bg-gray-900 flex items-center justify-center">
            <p className="text-gray-500 text-sm animate-pulse">Loading map…</p>
          </div>
        ) : (
          <EventsMap events={mapPoints} />
        )}
      </div>

      {/* ── Category filter ── */}
      <div className="flex flex-wrap gap-2">
        {CATEGORY_FILTERS.map((f) => (
          <button
            key={f.id}
            onClick={() => setCategory(f.id)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              category === f.id
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
            }`}
          >
            {f.label}
          </button>
        ))}
        {events.length > 0 && (
          <span className="ml-auto text-xs text-gray-500 self-center">
            {events.length} active event{events.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* ── Events grid ── */}
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {!loading && !error && events.length === 0 && (
        <p className="text-gray-400 text-sm">No open events found for this filter.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {events.map((ev) => {
          const last = ev.geometry?.[ev.geometry.length - 1];
          const coords = last?.coordinates;
          const date = last?.date?.slice(0, 10);
          const cat = ev.categories?.[0];
          const dotColor = CAT_DOT[cat?.id ?? ""] ?? "bg-gray-500";

          return (
            <Link
              key={ev.id}
              href={`/events/${ev.id}`}
              className="group flex items-start gap-3 bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-blue-500 transition-colors"
            >
              {/* Category dot */}
              <span className={`mt-1 shrink-0 w-2.5 h-2.5 rounded-full ${dotColor}`} />

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-white text-sm leading-snug truncate">
                    {ev.title}
                  </h3>
                  <span className="shrink-0 text-xs bg-gray-800 px-2 py-0.5 rounded-full text-gray-300">
                    {cat?.title ?? "Unknown"}
                  </span>
                </div>
                {coords && (
                  <p className="text-xs text-gray-500 mt-1">
                    {coords[1].toFixed(2)}°, {coords[0].toFixed(2)}° · {date}
                  </p>
                )}
                <p className="text-xs text-blue-400 mt-2 font-medium group-hover:underline">
                  View situation brief →
                </p>
              </div>
            </Link>
          );
        })}
      </div>

    </div>
  );
}
