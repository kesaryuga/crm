/** @type {import('next').NextConfig} */
function resolveApiTarget() {
  let raw = (
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "https://crm-backend-myq6.onrender.com"
  )
    .trim()
    .replace(/\/+$/, "");

  if (!/^https?:\/\//i.test(raw)) {
    raw = `https://${raw}`;
  }

  try {
    const host = new URL(raw).hostname;
    // Render `fromService.host` may return "crm-backend-myq6" without domain
    if (/^[a-z0-9-]+$/i.test(host)) {
      raw = `https://${host}.onrender.com`;
    }
  } catch {
    raw = "https://crm-backend-myq6.onrender.com";
  }

  return raw;
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
