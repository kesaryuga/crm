"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Me = {
  email: string;
  first_name: string;
  last_name: string;
  role: string | null;
  permissions: string[];
};

export default function DashboardPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [health, setHealth] = useState<string>("…");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const meRes = await fetch("/api/v1/auth/me", { credentials: "include" });
        if (meRes.status === 401) {
          window.location.href = "/login";
          return;
        }
        if (!meRes.ok) {
          if (!cancelled) setError("Не удалось загрузить профиль");
          return;
        }
        const meBody = (await meRes.json()) as Me;
        if (!cancelled) setMe(meBody);

        const healthRes = await fetch("/health/ready", { credentials: "include" });
        const healthBody = await healthRes.json().catch(() => ({}));
        if (!cancelled) {
          setHealth(
            healthRes.ok
              ? `ready: ${JSON.stringify(healthBody)}`
              : `not ready (${healthRes.status})`,
          );
        }
      } catch {
        if (!cancelled) setError("API недоступен");
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function logout() {
    await fetch("/api/v1/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    window.location.href = "/login";
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-6 px-6">
      <h1 className="text-3xl font-semibold tracking-tight">CRM · кабинет</h1>
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
      {me ? (
        <div className="rounded-md border border-line p-4 text-sm">
          <p className="font-medium">
            {me.last_name} {me.first_name}
          </p>
          <p className="text-muted">{me.email}</p>
          <p className="mt-2">Роль: {me.role || "—"}</p>
          <p className="mt-1 break-words">
            Права: {me.permissions.length ? me.permissions.join(", ") : "—"}
          </p>
        </div>
      ) : null}
      <p className="text-sm text-muted">Health: {health}</p>
      <div className="flex gap-3">
        <Link
          href="/"
          className="inline-flex h-11 items-center justify-center rounded-md border border-line px-5"
        >
          На главную
        </Link>
        <button
          type="button"
          onClick={logout}
          className="h-11 rounded-md bg-accent px-5 text-white transition hover:opacity-90"
        >
          Выйти
        </button>
      </div>
    </main>
  );
}
