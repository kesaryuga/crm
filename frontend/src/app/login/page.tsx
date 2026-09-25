"use client";

import { FormEvent, useState } from "react";

function extractMessage(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object" && "message" in detail) {
    const m = (detail as { message?: unknown }).message;
    if (typeof m === "string") return m;
  }
  if (status === 401) return "Неверный email или пароль";
  if (status === 429) return "Слишком много попыток. Подождите минуту.";
  if (status === 502 || status === 503 || status === 504) {
    return "Сервис запускается — подождите 30 секунд и нажмите «Войти» ещё раз";
  }
  return `Не удалось войти (ошибка ${status})`;
}

export default function LoginPage() {
  const [email, setEmail] = useState("admin@kit-lab.by");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function attempt(body: string): Promise<Response> {
    return fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body,
    });
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    const payload = JSON.stringify({
      email: email.trim(),
      password: password,
    });
    try {
      let res = await attempt(payload);
      // Cold start on Render Free often returns 502 — retry twice
      for (let i = 0; i < 2 && (res.status === 502 || res.status === 503); i++) {
        await new Promise((r) => setTimeout(r, 2500));
        res = await attempt(payload);
      }
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setError(extractMessage(res.status, body));
        return;
      }
      window.location.href = "/dashboard";
    } catch {
      setError("Сервис запускается — подождите 30 секунд и нажмите «Войти» ещё раз");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-6">
      <h1 className="text-2xl font-semibold tracking-tight">Вход в CRM</h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1.5 text-sm">
          Email
          <input
            type="email"
            name="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="h-11 rounded-md border border-line bg-white px-3"
          />
        </label>
        <label className="flex flex-col gap-1.5 text-sm">
          Пароль
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="h-11 rounded-md border border-line bg-white px-3"
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="h-11 rounded-md bg-accent px-5 text-white transition hover:opacity-90 disabled:opacity-60"
        >
          {loading ? "Входим…" : "Войти"}
        </button>
        {error ? (
          <p role="alert" className="text-sm text-red-700">
            {error}
          </p>
        ) : null}
        <p className="text-xs text-muted">
          Тестовый вход: admin@kit-lab.by · пароль kitlab2026
        </p>
      </form>
    </main>
  );
}
