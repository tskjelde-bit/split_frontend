"""QA-overlay: rentegning (50% opacity) over original-crop. Bruk: make_qa.py H0101"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand
import fixtures

# 200dpi-render av 1:100-tegning: 1 px = 1.27 cm virkelig -> 1 cm = 0.7874 px
PNG_PX_PER_CM = 200 / 2.54 / 100


def main():
    uid = sys.argv[1]
    crop = brand.UNDERLAG / f"{uid}-crop.png"
    plan = brand.RENTEGNING / f"{uid}-plan.svg"
    html = f"""<!DOCTYPE html><html><head><style>
body {{ margin: 0; background: #888; }}
.stack {{ position: relative; display: inline-block; }}
.stack img {{ display: block; }}
.stack svg {{ position: absolute; left: 0; top: 0; opacity: 0.55; }}
</style></head><body><div class="stack">
<img src="file://{crop}">
<svg xmlns="http://www.w3.org/2000/svg" style="transform-origin: 0 0;">
{fixtures.DEFS}
<g transform="scale({PNG_PX_PER_CM:.4f})">{plan.read_text()}</g>
</svg>
</div></body></html>"""
    brand.QA.mkdir(exist_ok=True)
    out = brand.QA / f"{uid}-overlay.html"
    out.write_text(html)
    print(out)


if __name__ == "__main__":
    main()
