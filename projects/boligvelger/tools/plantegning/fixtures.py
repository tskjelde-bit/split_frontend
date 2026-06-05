"""SVG <defs>-symboler for møblering og fast innredning. Alle mål i cm."""

INK = "#1A1A18"

DEFS = f"""<defs>
  <!-- WC: 40x65cm -->
  <g id="wc">
    <rect x="5" y="0" width="30" height="20" rx="3" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <ellipse cx="20" cy="42" rx="16" ry="21" fill="none" stroke="{INK}" stroke-width="1.2"/>
  </g>
  <!-- Servant: 50x40cm -->
  <g id="servant">
    <rect x="0" y="0" width="50" height="40" rx="4" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <ellipse cx="25" cy="20" rx="16" ry="11" fill="none" stroke="{INK}" stroke-width="1"/>
    <circle cx="25" cy="7" r="2" fill="{INK}"/>
  </g>
  <!-- Dusj: 90x90cm med diagonal og sluk -->
  <g id="dusj">
    <rect x="0" y="0" width="90" height="90" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <line x1="0" y1="90" x2="90" y2="0" stroke="{INK}" stroke-width="0.6" stroke-dasharray="4 3"/>
    <circle cx="45" cy="45" r="3" fill="none" stroke="{INK}" stroke-width="0.8"/>
  </g>
  <!-- Seng 140: 140x200cm -->
  <g id="seng140">
    <rect x="0" y="0" width="140" height="200" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <rect x="8" y="8" width="58" height="40" rx="6" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <rect x="74" y="8" width="58" height="40" rx="6" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <line x1="0" y1="60" x2="140" y2="60" stroke="{INK}" stroke-width="0.6"/>
  </g>
  <!-- Sofa 2-seter: 160x85cm -->
  <g id="sofa">
    <rect x="0" y="0" width="160" height="85" rx="10" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <line x1="14" y1="22" x2="146" y2="22" stroke="{INK}" stroke-width="0.7"/>
    <line x1="80" y1="22" x2="80" y2="85" stroke="{INK}" stroke-width="0.7"/>
  </g>
  <!-- Spisebord m/2 stoler: 120x75cm bord -->
  <g id="bord2">
    <rect x="0" y="20" width="120" height="75" fill="none" stroke="{INK}" stroke-width="1.2"/>
    <rect x="32" y="0" width="45" height="16" rx="4" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <rect x="32" y="99" width="45" height="16" rx="4" fill="none" stroke="{INK}" stroke-width="0.8"/>
  </g>
  <!-- Kjøkkenbenk-segment 60cm dyp, 60cm bred m/komfyrtopp -->
  <g id="komfyr">
    <rect x="0" y="0" width="60" height="60" fill="none" stroke="{INK}" stroke-width="1"/>
    <circle cx="18" cy="18" r="9" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <circle cx="42" cy="18" r="9" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <circle cx="18" cy="42" r="9" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <circle cx="42" cy="42" r="9" fill="none" stroke="{INK}" stroke-width="0.8"/>
  </g>
  <!-- Kjøkkenvask-segment 60x60cm -->
  <g id="kvask">
    <rect x="0" y="0" width="60" height="60" fill="none" stroke="{INK}" stroke-width="1"/>
    <rect x="12" y="12" width="36" height="36" rx="4" fill="none" stroke="{INK}" stroke-width="0.8"/>
    <circle cx="30" cy="8" r="2" fill="{INK}"/>
  </g>
  <!-- Garderobeskap-segment 60x60cm -->
  <g id="skap">
    <rect x="0" y="0" width="60" height="60" fill="none" stroke="{INK}" stroke-width="1"/>
    <line x1="0" y1="0" x2="60" y2="60" stroke="{INK}" stroke-width="0.5"/>
  </g>
  <!-- Rundt spisebord Ø90 -->
  <g id="rundbord90">
    <circle cx="45" cy="45" r="45" fill="none" stroke="{INK}" stroke-width="1.2"/>
  </g>
  <!-- Rundt sofabord Ø60 -->
  <g id="sofabord60">
    <circle cx="30" cy="30" r="30" fill="none" stroke="{INK}" stroke-width="1"/>
  </g>
  <!-- Lenestol 70x70cm -->
  <g id="lenestol">
    <rect x="0" y="0" width="70" height="70" rx="14" fill="none" stroke="{INK}" stroke-width="1.1"/>
    <line x1="10" y1="18" x2="60" y2="18" stroke="{INK}" stroke-width="0.7"/>
  </g>
  <!-- Stol 45x45cm -->
  <g id="stol">
    <rect x="0" y="0" width="45" height="45" rx="8" fill="none" stroke="{INK}" stroke-width="0.9"/>
  </g>
</defs>"""


def door(x: float, y: float, width: float, angle: float = 0, sweep: int = 1) -> str:
    """Dørslag: åpning ved (x,y), dørblad-bredde i cm, rotasjon i grader.

    Tegner karmlinje + kvartsirkelbue. sweep=1 høyrehengslet, 0 venstre.
    """
    end_x, end_y = (x + width, y) if sweep else (x - width, y)
    arc_y = y + width
    d = f"M {x} {arc_y} A {width} {width} 0 0 {sweep} {end_x} {end_y}"
    return (
        f'<g transform="rotate({angle} {x} {y})">'
        f'<line x1="{x}" y1="{y}" x2="{x}" y2="{arc_y}" stroke="{INK}" stroke-width="1"/>'
        f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="0.7"/></g>'
    )
