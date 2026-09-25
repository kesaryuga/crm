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
  if (contentType) {
    headers.set("content-type", contentType);
  }

  const hasBody = req.method !== "GET" && req.method !== "HEAD";
  let body: string | undefined;
  if (hasBody) {
    body = await req.text();
    if (body && !headers.has("content-type")) {
      headers.set("content-type", "application/json");
    }
    // FastAPI needs an explicit content-length
    if (body) {
      headers.set("content-length", String(new TextEncoder().encode(body).length));
    }
  }

  try {
    const upstream = await fetch(url, {
      method: req.method,
      headers,
      body: hasBody ? body || undefined : undefined,
      redirect: "manual",
    });

    const text = await upstream.text();
    const responseHeaders = new Headers();
    for (const [key, value] of upstream.headers.entries()) {
      if (key === "content-encoding" || key === "transfer-encoding" || key === "content-length") {
        continue;
      }
      responseHeaders.set(key, value);
    }
    // Preserve cookies from backend
    const setCookies = typeof upstream.headers.getSetCookie === "function"
      ? upstream.headers.getSetCookie()
      : [];
    for (const value of setCookies) {
      responseHeaders.append("set-cookie", value);
    }
    if (!responseHeaders.has("content-type")) {
      responseHeaders.set("content-type", "application/json; charset=utf-8");
    }

    return new NextResponse(text, {
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
