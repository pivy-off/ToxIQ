import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV === "development";
const backendUrl = process.env.BACKEND_URL || (isDev ? "http://127.0.0.1:8000" : "");

if (!backendUrl && !isDev) {
  console.warn("Warning: BACKEND_URL is not set. API requests will fail in production.");
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,

  async rewrites() {
    if (!backendUrl) {
      return [];
    }
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },

  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-DNS-Prefetch-Control", value: "on" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
