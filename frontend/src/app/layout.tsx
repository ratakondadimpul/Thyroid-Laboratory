import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Thyroid Lab Intelligence — AI-Powered Laboratory Analysis",
  description: "Upload → Analyze → Classify → Visualize → Download → Track History. Thyroid laboratory intelligence platform.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen">
        {children}
      </body>
    </html>
  );
}
