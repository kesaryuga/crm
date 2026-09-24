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

async function proxy(req: NextRequest, prefix: string, path: string[]): Promise<Response> {
  const targetPath = path.map(encodeURIComponent).join("/");
  const url = `${resolveApiTarget()}${prefix}/${targetPath}${req.nextUrl.search}`;

  const headers = new Headers();
  const cookie = req.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  const hasBody = req.method !== "GET" && req.method !== "HEAD";
  const init: RequestInit = { method: req.method, headers };
  if (hasBody) {
    init.body = await req.arrayBuffer();
  }

  try {
    const upstream = await fetch(url, init);
    const body = await upstream.arrayBuffer();
    const responseHeaders = new Headers();
    const setCookie = upstream.headers.getSetCookie?.() ?? [];
    for (const value of setCookie) {
      responseHeaders.append("set-cookie", value);
    }
    const ct = upstream.headers.get("content-type");
    if (ct) responseHeaders.set("content-type", ct);
    return new NextResponse(body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch (err) {
    return NextResponse.json(
      {
        detail: {
          code: "PROXY_ERROR",
          message: String(err),
          url,
        },
      },
      { status: 502 },
    );
  }
}

export async function GET(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, "/api", path);
}

export async function POST(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, "/api", path);
}

export async function PUT(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, "/api", path);
}

export async function PATCH(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, "/api", path);
}

export async function DELETE(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, "/api", path);
}
