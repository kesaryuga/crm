# Архитектура (Sprint 0)

Модульный монолит: `frontend` (Next.js) + `backend` (FastAPI) + `postgres` + volume `uploads`.

- Бизнес-логика не знает о физическом storage (Local / S3-compatible).
- Номера договоров и протоколов — **вручную**, со сбросом года; уникальность `(type, year, number)`.
- Бесплатный хостинг — временный слой; перенос на VPS = Docker Compose + restore dump/файлов.
