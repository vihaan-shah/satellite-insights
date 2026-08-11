"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import InsightCard from "@/components/InsightCard";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

interface Event {
  id: string;
  title: string;
  categories: { id: string; title: string }[];
  geometry: { date: string; coordinates: [number, number] }[];
  status: string;
}

interface Insight {
  event_id: string;
  title: string;
  brief: string;
  imagery_url: string;
  hotspot_count: number;
  analysis: Record<string, unknown>;
  categories: string[];
}

const CATEGORY_FILTERS = [
  { id: "", label: "All Events" },
  { id: "wildfires", label: "🔥 Wildfires" },
  { id: "floods", label: "🌊 Floods" },
  { id: "severeStorms", label: "⛈ Storms" },
  { id: "volcanoes", label: "🌋 Volcanoes" },
];

export default function DashboardPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    const url = category
      ? `${API}/events?category=${category}&limit=20`
      : `${API}/events?limit=20`;

    fetch(url)
      .then((r) => r.json())
      .then((data) => setEvents(Array.isArray(data) ? data : []))
      .catch(() => setError("Failed to load events. Is the backend running?"))
      .finally(() => setLoading(false));
  }, [category]);

  useEffect(() => {
    fetch(`${API}/insights?limit=6`)
      .then((r) => r.json())
      .then((data) => setInsights(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Active Natural Events</h1>
        <p className="text-gray-400 mt-1">
          Real-time data from NASA EONET · Click an event to generate an AI situation brief
        </p>
      </div>

      {/* Category filter */}
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
      </div>

      {/* Latest AI Briefs */}
      {insights.length > 0 && (
        <section>
          <h2 className="text-xl font-semibold text-gray-200 mb-3">Latest Situation Briefs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {insights.map((ins) => (
              <InsightCard key={ins.event_id} insight={ins} />
            ))}
          </div>
        </section>
      )}

      {/* Events list */}
      <section>
        <h2 className="text-xl font-semibold text-gray-200 mb-3">Events Feed</h2>
        {loading && <p className="text-gray-400">Loading events…</p>}
        {error && <p className="text-red-400">{error}</p>}
        {!loading && !error && events.length === 0 && (
          <p className="text-gray-400">No open events found for this filter.</p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {events.map((ev) => {
            const coords = ev.geometry?.[ev.geometry.length - 1]?.coordinates;
            const date = ev.geometry?.[ev.geometry.length - 1]?.date?.slice(0, 10);
            const cat = ev.categories?.[0]?.title ?? "Unknown";
            return (
              <Link
                key={ev.id}
                href={`/events/${ev.id}`}
                className="block bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-blue-500 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-white text-sm leading-snug">{ev.title}</h3>
                  <span className="shrink-0 text-xs bg-gray-800 px-2 py-0.5 rounded-full text-gray-300">
                    {cat}
                  </span>
                </div>
                {coords && (
                  <p className="text-xs text-gray-500 mt-2">
                    {coords[1].toFixed(2)}°, {coords[0].toFixed(2)}° · {date}
                  </p>
                )}
                <p className="text-xs text-blue-400 mt-3 font-medium">View brief →</p>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
