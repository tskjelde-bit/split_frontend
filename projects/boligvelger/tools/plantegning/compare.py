"""Side-ved-side + overlay-sammenligning: arkitekt-crop vs ren rentegning.

Bruk: compare.py H0101 [OFFX OFFY]  ->  skriver qa/H0101-compare.html
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import brand
import build_pages
import fixtures

PNG_PX_PER_CM = 200 / 2.54 / 100  # 0.7874


def main():
    uid = sys.argv[1]
    offx = sys.argv[2] if len(sys.argv) > 2 else "0"
    offy = sys.argv[3] if len(sys.argv) > 3 else "0"
    crop = brand.UNDERLAG / f"{uid}-crop.png"
    plan = brand.RENTEGNING / f"{uid}-plan.svg"
    vb, inner = build_pages.load_fragment(plan)
    w = vb[2] * PNG_PX_PER_CM
    h = vb[3] * PNG_PX_PER_CM
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {vb[2]:.0f} {vb[3]:.0f}">{fixtures.DEFS}{inner}</svg>'
    )
    html = f"""<!DOCTYPE html><html><head><style>
body {{ margin: 0; background: #777; font-family: Helvetica; }}
.row {{ display: flex; gap: 14px; align-items: flex-start; padding: 10px; }}
.cell {{ background: #FBFAF6; }}
.stack {{ position: relative; }}
.stack svg {{ position: absolute; left: {offx}px; top: {offy}px; opacity: 0.55; }}
h4 {{ color: #eee; margin: 2px 0 4px; font-size: 12px; font-weight: normal; }}
</style></head><body>
<div class="row">
  <div><h4>arkitekt</h4><img src="file://{crop}"></div>
  <div><h4>rentegning</h4><div class="cell">{svg}</div></div>
  <div><h4>overlay</h4><div class="stack"><img src="file://{crop}">{svg}</div></div>
</div></body></html>"""
    out = brand.QA / f"{uid}-compare.html"
    out.write_text(html)
    print(out)


if __name__ == "__main__":
    main()
