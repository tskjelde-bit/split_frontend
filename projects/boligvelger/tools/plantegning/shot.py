"""Robust headless-Chrome screenshot: starter isolert Chrome, venter på fil, dreper prosessen.

Bruk: shot.py <url-eller-fil> <out.png> [WxH]
"""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def shot(target: str, out: str, size: str = "794,1123", timeout: float = 25.0) -> None:
    if "://" not in target:
        target = f"file://{Path(target).resolve()}"
    out_path = Path(out)
    out_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="chrome-shot-") as profile:
        proc = subprocess.Popen(
            [CHROME, "--headless=new", f"--user-data-dir={profile}",
             "--disable-gpu", f"--screenshot={out_path}",
             f"--window-size={size}", target],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + timeout
        try:
            while time.time() < deadline:
                if out_path.exists() and out_path.stat().st_size > 0:
                    time.sleep(0.4)  # la Chrome bli ferdig med å skrive
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.2)
        finally:
            proc.kill()
            proc.wait()
    if not out_path.exists():
        sys.exit(f"FEIL: ingen screenshot for {target}")
    print(out_path)


if __name__ == "__main__":
    size = sys.argv[3].replace("x", ",") if len(sys.argv) > 3 else "794,1123"
    shot(sys.argv[1], sys.argv[2], size)
