"""Houeland brand v4 constants and font embedding for plantegning pipeline."""
import base64
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EIENDOM = REPO / "eiendommer" / "dybwads gate 8"
ARKITEKT = EIENDOM / "arkitekt"
UNDERLAG = EIENDOM / "underlag"
RENTEGNING = EIENDOM / "rentegning"
OUTPUT = EIENDOM / "plantegninger"
QA = EIENDOM / "qa"
FONT_DIR = REPO / "brand houeland 2-0" / "01 Fonter"

# Farger (stil B — grønn signatur)
GREEN = "#1E3D2B"
BRICK = "#8A3324"
CARAMEL = "#C58B53"
CREAM = "#FBFAF6"
BEIGE = "#EFE9DC"
INK = "#1A1A18"
ROOM_FILL = "#F4F1E8"
HEMS_FILL = "#E5D3BC"
TILE_FILL = "#DCE2D6"
MUTED = "#8C8678"
LIGHT_LINE = "#DDD7C8"
HEADER_TEXT = "#F2EFE8"
HEADER_MUTED = "#C9C2AE"

# Skala: A4-side er 794x1123 px (96dpi). 1:50 → 1 virkelig cm = 0.7562 px.
A4_W, A4_H = 794, 1123
PX_PER_CM = (A4_W / 21.0) / 50.0  # 0.75619...


def _font_b64(filename: str) -> str:
    return base64.b64encode((FONT_DIR / filename).read_bytes()).decode()


def font_css() -> str:
    """@font-face-blokk med base64-embeddede brand-fonter."""
    sfizia = _font_b64("Sfizia-Regular.otf")
    engravers = _font_b64("Engravers' Gothic Regular.otf")
    return (
        "@font-face{font-family:'Sfizia';"
        f"src:url(data:font/otf;base64,{sfizia}) format('opentype');}}\n"
        "@font-face{font-family:'Engravers';"
        f"src:url(data:font/otf;base64,{engravers}) format('opentype');}}"
    )
