import { NextRequest, NextResponse } from "next/server";

const API_TARGET = (
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "https://crm-backend-myq6.onrender.com"
).replace(/\/$/, "");

export async function GET(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  const { path } = await ctx.params;
  const targetPath = path.map(encodeURIComponent).join("/");
  const upstream = await fetch(`${API_TARGET}/health/${targetPath}`, {
    method: "GET",
    headers: { cookie: req.headers.get("cookie") || "" },
  });
  const body = await upstream.text();
  return new NextResponse(body, {
    status: upstream.status,
    headers: { "content-type": "application/json" },
  });
}
