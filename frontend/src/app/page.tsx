import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-6 px-6">
      <h1 className="text-3xl font-semibold tracking-tight">CRM</h1>
      <p className="text-muted">
        Sprint 0: каркас приложения. Договоры, протоколы и контрагенты появятся в следующих
        спринтах.
      </p>
      <Link
        href="/login"
        className="inline-flex h-11 items-center justify-center rounded-md bg-accent px-5 text-white transition hover:opacity-90"
      >
        Войти
      </Link>
    </main>
  );
}
