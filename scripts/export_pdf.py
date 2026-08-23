"""
PDF/PNG Export Script.

Uses Playwright (headless Chromium) to screenshot the running dashboard
and save a management-ready PDF report.

Prerequisites:
    pip install playwright
    playwright install chromium

Usage:
    # Ensure the dashboard is running first:
    python src/dashboard/app.py --demo

    # Then in another terminal:
    python scripts/export_pdf.py
    python scripts/export_pdf.py --url http://localhost:8050 --out ./exports/report.pdf
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def export_dashboard(
    url: str = "http://localhost:8050",
    output_path: str | None = None,
    wait_seconds: int = 5,
    format: str = "pdf",
) -> Path:
    """
    Screenshot the dashboard and save as PDF or PNG.

    Args:
        url:          Dashboard URL.
        output_path:  Where to save the file. Auto-generated if None.
        wait_seconds: How long to wait for the page to fully render.
        format:       'pdf' or 'png'

    Returns:
        Path to the saved file.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright is not installed.")
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    export_dir = Path(os.getenv("EXPORT_DIR", "./exports"))
    export_dir.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = str(export_dir / f"ninjaone_compliance_{ts}.{format}")

    print(f"  → Connecting to {url} ...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url, wait_until="networkidle")

        print(f"  → Waiting {wait_seconds}s for dashboard to render...")
        time.sleep(wait_seconds)

        if format == "pdf":
            page.pdf(
                path=output_path,
                format="A3",
                landscape=True,
                margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
                print_background=True,
            )
        else:
            page.screenshot(
                path=output_path,
                full_page=True,
            )

        browser.close()

    print(f"  ✓ Exported: {output_path}")
    return Path(output_path)


def main():
    parser = argparse.ArgumentParser(description="Export NinjaOne Dashboard to PDF/PNG")
    parser.add_argument("--url", default="http://localhost:8050")
    parser.add_argument("--out", default=None)
    parser.add_argument("--wait", type=int, default=5)
    parser.add_argument("--format", choices=["pdf", "png"], default="pdf")
    args = parser.parse_args()

    print("\n📄 NinjaOne Dashboard Export")
    print("=" * 40)

    out = export_dashboard(
        url=args.url,
        output_path=args.out,
        wait_seconds=args.wait,
        format=args.format,
    )
    print(f"\n✅ Report saved to: {out}\n")


if __name__ == "__main__":
    main()
