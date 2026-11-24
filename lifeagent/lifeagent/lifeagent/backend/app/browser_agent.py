"""Agentic browser: a real Chromium (Playwright) fills and submits the form like a human would.
Falls back to a simulated submit if Playwright is not installed, so the demo still completes."""
import os, time, random
from pathlib import Path

SHOTS = Path(__file__).parent / "static" / "shots"

async def fill_application(form: dict, scheme: dict) -> dict:
    base = os.getenv("PUBLIC_BASE", "http://localhost:8000")
    headed = os.getenv("DEMO_HEADED") == "1"
    stamp = int(time.time())
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            b = await p.chromium.launch(headless=not headed)
            pg = await b.new_page(viewport={"width": 1000, "height": 900})
            await pg.goto(f"{base}/portal?scheme={scheme['id']}&name={scheme['name']}")
            for field, val in form.items():
                await pg.fill(f"[name={field}]", str(val))
                if headed: await pg.wait_for_timeout(400)
            await pg.screenshot(path=str(SHOTS / f"{stamp}_filled.png"))
            await pg.click("#submit")
            await pg.wait_for_selector("#receipt")
            ref = (await pg.inner_text("#ref")).strip()
            await pg.screenshot(path=str(SHOTS / f"{stamp}_receipt.png"))
            await b.close()
        return {"mode": "browser", "reference": ref, "screenshot": f"/static/shots/{stamp}_receipt.png"}
    except Exception as e:
        return {"mode": "simulated", "reference": f"LA-{random.randint(100000, 999999)}", "screenshot": None, "note": str(e)[:200]}
