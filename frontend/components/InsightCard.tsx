import Link from "next/link";

interface Insight {
  event_id: string;
  title: string;
  brief: string;
  imagery_url: string;
  hotspot_count: number;
  analysis: {
    estimated_area_ha?: number;
    risk_level?: string;
  };
  categories: string[];
}

const RISK_BORDER: Record<string, string> = {
  low: "border-green-700",
  medium: "border-yellow-600",
  high: "border-orange-600",
  critical: "border-red-600",
};

const RISK_BADGE: Record<string, string> = {
  low: "bg-green-900 text-green-300",
  medium: "bg-yellow-900 text-yellow-300",
  high: "bg-orange-900 text-orange-300",
  critical: "bg-red-900 text-red-300",
};

export default function InsightCard({ insight }: { insight: Insight }) {
  const risk = insight.analysis?.risk_level ?? "low";

  return (
    <Link
      href={`/events/${insight.event_id}`}
      className={`block bg-gray-900 border rounded-xl overflow-hidden hover:shadow-lg hover:shadow-blue-900/20 transition-all ${RISK_BORDER[risk] ?? "border-gray-800"}`}
    >
      {/* Imagery thumbnail */}
      {insight.imagery_url && (
        <div className="h-28 bg-gray-800 overflow-hidden">
          <img
            src={insight.imagery_url}
            alt="Satellite imagery"
            className="w-full h-full object-cover"
            onError={(e) => (e.currentTarget.parentElement!.style.display = "none")}
          />
        </div>
      )}

      <div className="p-4 space-y-2">
        {/* Title + risk badge */}
        <div className="flex items-start gap-2">
          <h3 className="text-sm font-semibold text-white leading-snug flex-1">
            {insight.title}
          </h3>
          <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${RISK_BADGE[risk] ?? ""}`}>
            {risk.toUpperCase()}
          </span>
        </div>

        {/* Brief excerpt */}
        <p className="text-xs text-gray-400 leading-relaxed line-clamp-3">
          {insight.brief}
        </p>

        {/* Stats */}
        <div className="flex gap-4 pt-1">
          <span className="text-xs text-gray-500">
            🔥 {insight.hotspot_count} hotspots
          </span>
          {insight.analysis?.estimated_area_ha ? (
            <span className="text-xs text-gray-500">
              📐 ~{insight.analysis.estimated_area_ha} ha
            </span>
          ) : null}
        </div>

        <p className="text-xs text-blue-400 font-medium pt-1">View full brief →</p>
      </div>
    </Link>
  );
}
