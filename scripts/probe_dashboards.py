# Minimal headless probe of free deploy dashboards (no long browser session).
# Prints final URL + title so we can see login state.

import asyncio
import sys


async def main() -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("NO_PLAYWRIGHT")
        return 2

    urls = sys.argv[1:] or [
        "https://supabase.com/dashboard",
        "https://dashboard.render.com",
        "https://railway.app",
    ]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        for url in urls:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(2500)
                print(f"URL={page.url}")
                print(f"TITLE={await page.title()}")
                snippet = (await page.inner_text("body"))[:400].replace("\n", " | ")
                print(f"TEXT={snippet}")
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL {url} {exc}")
            print("---")
        await browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
