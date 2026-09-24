/** @type {import('next').NextConfig} */
function resolveApiTarget() {
  const raw =
    process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  if (raw.startsWith("http://") || raw.startsWith("https://")) return raw;
  return `https://${raw}`;
}

const apiTarget = resolveApiTarget();

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${apiTarget}/api/:path*` },
      { source: "/health/:path*", destination: `${apiTarget}/health/:path*` },
    ];
  },
};

export default nextConfig;
