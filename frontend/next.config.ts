import type { NextConfig } from "next";
const isFirebaseBuild = process.env.FIREBASE_BUILD === "true";
const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Warm newsprint build: no export for Vercel (SSR), static export for Firebase
  ...(isFirebaseBuild ? { output: "export" as const, images: { unoptimized: true } } : {}),
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  async rewrites() {
    // In production on Vercel/Firebase, frontend calls backend directly via NEXT_PUBLIC_API_URL
    // Only proxy to localhost in development when backendUrl is local
    const isLocal = backendUrl.includes("127.0.0.1") || backendUrl.includes("localhost");
    if (!isLocal) return [];
    return [
      { source: "/api/:path*", destination: `${backendUrl}/api/:path*` },
      { source: "/health", destination: `${backendUrl}/health` }
    ];
  },
};
export default nextConfig;
