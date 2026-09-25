"use client";

import { FormEvent, useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        const message =
          body?.detail?.message || body?.detail || "Не удалось войти";
        setError(typeof message === "string" ? message : "Не удалось войти");
        return;
      }
      window.location.href = "/dashboard";
    } catch {
      setError("Сервис просыпается — подождите 30 секунд и нажмите «Войти» ещё раз.");
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
      </form>
    </main>
  );
}
