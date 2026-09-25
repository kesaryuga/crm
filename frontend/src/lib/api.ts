export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

function messageFromDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    const d = detail as { message?: string; detail?: string };
    if (typeof d.message === "string") return d.message;
    if (typeof d.detail === "string") return d.detail;
    if (Array.isArray(detail)) {
      return detail
        .map((e) => (e && typeof e === "object" && "msg" in e ? String(e.msg) : ""))
        .filter(Boolean)
        .join("; ");
    }
  }
  return "Ошибка запроса";
}

export async function api<T = unknown>(
  path: string,
  init?: RequestInit & { json?: unknown },
): Promise<T> {
  const { json, headers, ...rest } = init ?? {};
  const res = await fetch(path.startsWith("http") ? path : `/api/v1${path}`, {
    credentials: "include",
    headers: {
      ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(headers as Record<string, string> | undefined),
    },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
    ...rest,
  });

  if (res.status === 401) {
    if (typeof window !== "undefined" && !path.includes("/auth/")) {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Нет сессии");
  }

  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    throw new ApiError(res.status, messageFromDetail(data ?? text));
  }
  return data as T;
}

export const apiGet = <T,>(path: string) => api<T>(path);
export const apiPost = <T,>(path: string, json?: unknown) => api<T>(path, { method: "POST", json });
export const apiPatch = <T,>(path: string, json?: unknown) => api<T>(path, { method: "PATCH", json });
export const apiPut = <T,>(path: string, json?: unknown) => api<T>(path, { method: "PUT", json });
export const apiDelete = <T,>(path: string) => api<T>(path, { method: "DELETE" });
