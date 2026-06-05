"""Ekstraher vektor-SVG og 200dpi PNG underlag fra arkitekt-PDFene."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand

SOURCES = {
    1: ["Plan_1_etasje.pdf", "Boenheter_1etasje.pdf"],
    2: ["Plan_2_etasje.pdf", "Boenheter_2_etasje.pdf"],
    3: ["Plan_3_etasje.pdf", "Boenheter_3_etasje.pdf"],
}


def main():
    brand.UNDERLAG.mkdir(exist_ok=True)
    for floor, files in SOURCES.items():
        for pdf_name in files:
            src = brand.ARKITEKT / pdf_name
            stem = f"etasje-{floor}-{'plan' if pdf_name.startswith('Plan') else 'boenheter'}"
            svg_out = brand.UNDERLAG / f"{stem}.svg"
            png_prefix = brand.UNDERLAG / stem
            subprocess.run(["pdftocairo", "-svg", str(src), str(svg_out)], check=True)
            subprocess.run(
                ["pdftoppm", "-png", "-r", "200", str(src), str(png_prefix)],
                check=True,
            )
            print(f"{stem}: svg={svg_out.stat().st_size}b")


if __name__ == "__main__":
    main()
