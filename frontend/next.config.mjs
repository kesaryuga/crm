/** @type {import('next').NextConfig} */
function resolveApiTarget() {
  const raw =
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "https://crm-backend-myq6.onrender.com";
  if (raw.startsWith("http://") || raw.startsWith("https://")) return raw;
  return `https://${raw}`;
}

const apiTarget = resolveApiTarget();

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // Route handlers in src/app/api and src/app/health do the proxy.
  // Keep rewrites as a fallback for any path not covered by handlers.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiTarget}/api/:path*`,
      },
      {
        source: "/health/:path*",
        destination: `${apiTarget}/health/:path*`,
      },
    ];
  },
};

export default nextConfig;
