import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Satellite Insights",
  description: "Live satellite events → AI situation briefs via IBM Granite",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen font-sans antialiased">
        <nav className="border-b border-gray-800 px-6 py-3 flex items-center gap-3">
          <span className="text-lg font-bold tracking-tight text-white">🛰 Satellite Insights</span>
          <span className="text-xs text-gray-500 ml-2">Powered by IBM Granite</span>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
