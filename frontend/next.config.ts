import type { NextConfig } from "next";

// Where the FastAPI service lives. Locally that's your machine on :8000.
// Inside docker compose it's the service named "api", so API_URL=http://api:8000.
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Any request the browser makes to /api/... gets forwarded to FastAPI by
  // the Next.js server. The browser only ever talks to :3000, so there is
  // no cross-origin problem to deal with.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
