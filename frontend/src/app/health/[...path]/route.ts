import { NextRequest, NextResponse } from "next/server";

function resolveApiTarget(): string {
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
    if (/^[a-z0-9-]+$/i.test(host)) {
      raw = `https://${host}.onrender.com`;
    }
  } catch {
    raw = "https://crm-backend-myq6.onrender.com";
  }
  return raw;
}

export async function GET(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  const targetPath = path.map(encodeURIComponent).join("/");
  const url = `${resolveApiTarget()}/health/${targetPath}`;
  try {
    const upstream = await fetch(url, {
      method: "GET",
      headers: { cookie: req.headers.get("cookie") || "" },
    });
    const body = await upstream.text();
    return new NextResponse(body, {
      status: upstream.status,
      headers: { "content-type": "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      { detail: { code: "PROXY_ERROR", message: String(err), url } },
      { status: 502 },
    );
  }
}
