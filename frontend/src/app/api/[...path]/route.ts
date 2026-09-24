import { NextRequest, NextResponse } from "next/server";

const API_TARGET = (
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://crm-backend-myq6.onrender.com"
).replace(/\/$/, "");

async function proxy(req: NextRequest, path: string[]): Promise<Response> {
  const targetPath = path.map(encodeURIComponent).join("/");
  const url = `${API_TARGET}/${targetPath}${req.nextUrl.search}`;

  const headers = new Headers();
  headers.set("content-type", req.headers.get("content-type") || "application/json");
  const cookie = req.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);

  const hasBody = req.method !== "GET" && req.method !== "HEAD";
  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
  };
  if (hasBody) {
    init.body = await req.arrayBuffer();
  }

  const upstream = await fetch(url, init);
  const body = await upstream.arrayBuffer();
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("transfer-encoding");
  responseHeaders.delete("content-length");

  return new NextResponse(body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export async function GET(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function POST(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function PUT(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function PATCH(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, path);
}

export async function DELETE(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  return proxy(req, path);
}
