#!/usr/bin/env python3
"""
Screenshot the Resume WebUI (all 4 tabs) and the output PDF using Playwright.

Usage:
    python scripts/screenshot_ui.py

Requires:
    pip install playwright
    python -m playwright install chromium
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_IMGS = REPO_ROOT / "docs" / "imgs"
OUTPUT_DIR = REPO_ROOT / "output"
FRONTEND_PORT = 5173
BACKEND_PORT = 8000
BASE_URL = f"http://localhost:{FRONTEND_PORT}"

# Ensure we're in the venv
VENV_PYTHON = REPO_ROOT / "venv" / "bin" / "python"
if VENV_PYTHON.exists():
    PYTHON = str(VENV_PYTHON)
else:
    PYTHON = sys.executable


def log(msg: str):
    print(f"  ▶ {msg}", flush=True)


def run(cmd: list[str], cwd: str | None = None, wait: bool = True) -> subprocess.Popen | None:
    """Run a command and return the Popen object."""
    print(f"  $ {' '.join(cmd)}", flush=True)
    proc = subprocess.Popen(
        cmd,
        cwd=cwd or str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if wait:
        out, err = proc.communicate()
        if proc.returncode != 0:
            print(f"  ⚠ stderr: {err[:500]}", flush=True)
        return None
    return proc


def wait_for_http(url: str, timeout: int = 30, interval: float = 0.5):
    """Wait until an HTTP endpoint responds."""
    import urllib.request
    import urllib.error

    for _ in range(int(timeout / interval)):
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(interval)
    return False


def ensure_playwright():
    """Check if playwright and chromium are available."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright && python -m playwright install chromium")
        return False


def start_ui() -> list[subprocess.Popen]:
    """Start backend and frontend servers, return process list."""
    procs = []

    # Kill any existing processes on our ports
    for port in [BACKEND_PORT, FRONTEND_PORT]:
        run(["kill", "-9", str(port)], wait=False)  # best effort
        run(["lsof", "-ti", f":{port}"], wait=False)
        subprocess.run(
            f"lsof -ti :{port} | xargs kill -9 2>/dev/null",
            shell=True,
        )

    time.sleep(0.5)

    # Start backend
    log(f"Starting backend on port {BACKEND_PORT}...")
    backend = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "ui.backend.main:app",
         "--host", "127.0.0.1", "--port", str(BACKEND_PORT)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    procs.append(backend)

    # Start frontend
    log(f"Starting frontend on port {FRONTEND_PORT}...")
    frontend = subprocess.Popen(
        ["npx", "vite", "--host", "--port", str(FRONTEND_PORT)],
        cwd=str(REPO_ROOT / "ui" / "frontend"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    procs.append(frontend)

    return procs


def stop_ui(procs: list[subprocess.Popen]):
    """Stop all server processes."""
    for proc in procs:
        proc.terminate()
    for proc in procs:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    # Clean up port processes
    for port in [BACKEND_PORT, FRONTEND_PORT]:
        subprocess.run(
            f"lsof -ti :{port} | xargs kill -9 2>/dev/null",
            shell=True,
        )


def take_screenshots(page, base_url: str):
    """Take screenshots of all tabs and save to docs/imgs/."""
    DOCS_IMGS.mkdir(parents=True, exist_ok=True)
    viewport = {"width": 1440, "height": 900}
    page.set_viewport_size(viewport)

    screenshots = {}

    # ── Tab 0: Resume ──
    log("Capture: Resume tab (tab 0)")
    page.goto(f"{base_url}/", wait_until="networkidle")
    time.sleep(1.5)  # let data load
    page.screenshot(path=str(DOCS_IMGS / "ui-resume-tab.png"), full_page=True)
    screenshots["resume"] = "ui-resume-tab.png"

    # ── Tab 1: Transform ──
    log("Capture: Transform tab (tab 1)")
    transform_tab = page.locator('button[aria-controls="tabpanel-1"]')
    if transform_tab.is_visible():
        transform_tab.click()
    else:
        # Click by tab index
        tabs = page.locator('[role="tab"]')
        tabs.nth(1).click()
    time.sleep(1.5)
    page.screenshot(path=str(DOCS_IMGS / "ui-transform-tab.png"), full_page=True)
    screenshots["transform"] = "ui-transform-tab.png"

    # ── Tab 2: Compare ──
    log("Capture: Compare tab (tab 2)")
    compare_tab = page.locator('button[aria-controls="tabpanel-2"]')
    if compare_tab.is_visible():
        compare_tab.click()
    else:
        tabs = page.locator('[role="tab"]')
        tabs.nth(2).click()
    time.sleep(1.0)
    page.screenshot(path=str(DOCS_IMGS / "ui-compare-tab.png"), full_page=True)
    screenshots["compare"] = "ui-compare-tab.png"

    # ── Tab 3: History ──
    log("Capture: History tab (tab 3)")
    history_tab = page.locator('button[aria-controls="tabpanel-3"]')
    if history_tab.is_visible():
        history_tab.click()
    else:
        tabs = page.locator('[role="tab"]')
        tabs.nth(3).click()
    time.sleep(1.5)
    page.screenshot(path=str(DOCS_IMGS / "ui-history-tab.png"), full_page=True)
    screenshots["history"] = "ui-history-tab.png"

    # ⚠️ Prevent screenshots_ manifest from being created
    # since we want a simple dict
    return screenshots


def screenshot_pdf():
    """Convert the first page of the output PDF to a PNG image."""
    pdf_dir = OUTPUT_DIR / "-principal-software-developer-202606"
    pdf_path = pdf_dir / "William_Jiang_CV.pdf"
    out_path = DOCS_IMGS / "output-resume-pdf.png"

    if not pdf_path.exists():
        log(f"⚠ PDF not found: {pdf_path}")
        return None

    log(f"Converting PDF to PNG: {pdf_path}")

    # Try pdf2image first (most reliable)
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=200)
        if images:
            images[0].save(str(out_path), "PNG")
            log(f"Saved PDF screenshot to {out_path}")
            return "output-resume-pdf.png"
    except ImportError:
        pass

    # Fallback: use macOS sips (built-in)
    # First convert PDF to JPEG using sips, then rename
    jpeg_path = out_path.with_suffix(".jpg")
    result = subprocess.run(
        ["sips", "-s", "format", "jpeg", "-Z", "1600",
         str(pdf_path), "--out", str(jpeg_path)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        # Rename to .png (it's a JPEG but good enough for docs)
        shutil.move(str(jpeg_path), str(out_path))
        log(f"Saved PDF screenshot to {out_path}")
        return "output-resume-pdf.png"

    log("⚠ Could not convert PDF to image")
    return None


def main():
    if not ensure_playwright():
        sys.exit(1)

    from playwright.sync_api import sync_playwright

    log("Starting UI servers...")
    procs = start_ui()

    try:
        # Wait for frontend
        log("Waiting for frontend...")
        if not wait_for_http(f"http://localhost:{FRONTEND_PORT}", timeout=45):
            log("❌ Frontend did not start in time")
            stop_ui(procs)
            sys.exit(1)

        # Wait for backend
        log("Waiting for backend...")
        if not wait_for_http(f"http://127.0.0.1:{BACKEND_PORT}/api/themes", timeout=30):
            log("❌ Backend did not start in time")
            stop_ui(procs)
            sys.exit(1)

        log("Both servers are ready. Taking screenshots...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=2,  # Retina quality
            )
            page = context.new_page()

            # Screenshot all UI tabs
            screenshot_map = take_screenshots(page, BASE_URL)

            browser.close()

        # Screenshot PDF output (conversion, not browser)
        pdf_screenshot = screenshot_pdf()

        log("✅ All screenshots saved to docs/imgs/")
        print("\nGenerated files:")
        for name, file in screenshot_map.items():
            print(f"  📷 docs/imgs/{file}  ({name})")
        if pdf_screenshot:
            print(f"  📷 docs/imgs/{pdf_screenshot}  (PDF example)")

    finally:
        stop_ui(procs)
        log("UI servers stopped.")


if __name__ == "__main__":
    main()
