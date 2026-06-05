"""Eksporter side-SVG til A4 PDF via isolert headless Chrome. Bruk: export_pdf.py [H0101 ...]"""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def chrome_pdf(html: Path, pdf: Path, timeout: float = 30.0) -> None:
    """Kjør Chrome printToPDF; vent på fila og drep prosessen (Chrome henger etter skriving)."""
    pdf.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="chrome-pdf-") as profile:
        proc = subprocess.Popen(
            [CHROME, "--headless=new", f"--user-data-dir={profile}",
             "--no-pdf-header-footer", f"--print-to-pdf={pdf}", f"file://{html}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + timeout
        try:
            while time.time() < deadline:
                if pdf.exists() and pdf.stat().st_size > 0:
                    time.sleep(0.5)
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.2)
        finally:
            proc.kill()
            proc.wait()
    if not pdf.exists():
        sys.exit(f"FEIL: ingen PDF for {html}")


def wrap_html(svg_path: Path) -> Path:
    html = f"""<!DOCTYPE html><html><head><style>
@page {{ size: A4; margin: 0; }}
html, body {{ margin: 0; padding: 0; }}
svg {{ display: block; width: 210mm; height: 297mm; }}
</style></head><body>{svg_path.read_text()}</body></html>"""
    out = Path("/tmp") / f"{svg_path.stem}-print.html"
    out.write_text(html)
    return out


def main():
    targets = sys.argv[1:] or sorted(p.stem for p in brand.OUTPUT.glob("H*.svg"))
    for uid in targets:
        svg = brand.OUTPUT / f"{uid}.svg"
        html = wrap_html(svg)
        pdf = brand.OUTPUT / f"{uid}.pdf"
        chrome_pdf(html, pdf)
        pages = subprocess.run(
            ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True
        ).stdout
        n = [l for l in pages.splitlines() if l.startswith("Pages:")][0].split()[-1]
        assert n == "1", f"{uid}: {n} sider!"
        print(f"{uid}.pdf OK (1 side, {pdf.stat().st_size}b)")


if __name__ == "__main__":
    main()
