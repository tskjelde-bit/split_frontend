#!/usr/bin/env python3
"""
Generate Snyteklut Forretningsplan 2026 as a professional A4 PDF.
Uses reportlab Platypus for document flow.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
import os

# ── Colour palette ──────────────────────────────────────────────
NAVY       = HexColor("#1A1A2E")
CREAM      = HexColor("#F5F0E8")
COPPER     = HexColor("#8B5E3C")
LIGHT_GRAY = HexColor("#F2F2F2")
MID_GRAY   = HexColor("#E0E0E0")
DARK_TEXT   = HexColor("#2C2C2C")
WHITE       = white

PAGE_W, PAGE_H = A4
LEFT_MARGIN  = 20 * mm
RIGHT_MARGIN = 20 * mm
TOP_MARGIN   = 35 * mm
BOT_MARGIN   = 22 * mm

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "Snyteklut_Forretningsplan.pdf")


# ── Page callbacks ──────────────────────────────────────────────
def draw_cover(canvas, doc):
    """Draw the full-page cover directly on the canvas (page 1)."""
    canvas.saveState()
    w, h = PAGE_W, PAGE_H

    # Full-page navy background
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, h, stroke=0, fill=1)

    # Accent stripe
    canvas.setFillColor(COPPER)
    canvas.rect(0, h * 0.42, w, 4 * mm, stroke=0, fill=1)

    # Title
    canvas.setFillColor(CREAM)
    canvas.setFont("Helvetica-Bold", 48)
    canvas.drawCentredString(w / 2, h * 0.62, "Snyteklut")

    canvas.setFont("Helvetica", 20)
    canvas.drawCentredString(w / 2, h * 0.55, "Forretningsplan 2026")

    # Tagline
    canvas.setFillColor(COPPER)
    canvas.setFont("Helvetica-Oblique", 16)
    canvas.drawCentredString(w / 2, h * 0.35, "Verdighet i hverdagen")

    # Description
    canvas.setFillColor(HexColor("#CCCCCC"))
    canvas.setFont("Helvetica", 12)
    canvas.drawCentredString(
        w / 2, h * 0.28,
        "Vaskbar, antibakteriell tekstilklut for rusrehabilitering"
    )

    # Bottom info
    canvas.setFillColor(HexColor("#888888"))
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(w / 2, h * 0.10, "Snyteklut AS (under stiftelse)  |  2026")

    canvas.restoreState()


def draw_later_pages(canvas, doc):
    """Draw header bar and footer on content pages."""
    canvas.saveState()
    w, h = PAGE_W, PAGE_H

    # Top bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 28 * mm, w, 28 * mm, stroke=0, fill=1)
    canvas.setFillColor(CREAM)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(20 * mm, h - 18 * mm, "Snyteklut")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(w - 20 * mm, h - 18 * mm, "Forretningsplan 2026")

    # Footer
    canvas.setFillColor(HexColor("#999999"))
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, 12 * mm, f"Side {doc.page}")
    canvas.drawRightString(w - 20 * mm, 12 * mm, "Snyteklut AS  |  Konfidensielt")

    canvas.restoreState()


# ── Styles ───────────────────────────────────────────────────────
_styles_cache = None

def build_styles():
    global _styles_cache
    if _styles_cache is not None:
        return _styles_cache

    ss = getSampleStyleSheet()

    ss.add(ParagraphStyle(
        "SectionTitle",
        parent=ss["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=NAVY,
        spaceBefore=18,
        spaceAfter=8,
        leading=18,
    ))
    ss.add(ParagraphStyle(
        "SubTitle",
        parent=ss["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=COPPER,
        spaceBefore=12,
        spaceAfter=4,
        leading=14,
    ))
    ss.add(ParagraphStyle(
        "Body",
        parent=ss["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_TEXT,
        leading=14,
        spaceBefore=2,
        spaceAfter=4,
    ))
    ss.add(ParagraphStyle(
        "BulletItem",
        parent=ss["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=DARK_TEXT,
        leading=14,
        leftIndent=16,
        bulletIndent=6,
        spaceBefore=1,
        spaceAfter=1,
    ))
    ss.add(ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=WHITE,
        alignment=TA_CENTER,
        leading=12,
    ))
    ss.add(ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=9,
        textColor=DARK_TEXT,
        alignment=TA_CENTER,
        leading=12,
    ))
    ss.add(ParagraphStyle(
        "TableCellLeft",
        fontName="Helvetica",
        fontSize=9,
        textColor=DARK_TEXT,
        alignment=TA_LEFT,
        leading=12,
    ))
    _styles_cache = ss
    return ss


# ── Table builder helpers ────────────────────────────────────────
def styled_table(data, col_widths=None, first_col_left=True):
    """Return a Table with professional alternating-row styling."""
    ss = build_styles()

    formatted = []
    for r_idx, row in enumerate(data):
        frow = []
        for c_idx, cell in enumerate(row):
            if isinstance(cell, str):
                if r_idx == 0:
                    frow.append(Paragraph(cell, ss["TableHeader"]))
                elif c_idx == 0 and first_col_left:
                    frow.append(Paragraph(cell, ss["TableCellLeft"]))
                else:
                    frow.append(Paragraph(cell, ss["TableCell"]))
            else:
                frow.append(cell)
        formatted.append(frow)

    t = Table(formatted, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.4, MID_GRAY),
        ("LINEBELOW", (0, 0), (-1, 0), 1, COPPER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    for i in range(1, len(data)):
        bg = LIGHT_GRAY if i % 2 == 0 else WHITE
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    t.setStyle(TableStyle(style_cmds))
    return t


def section_line():
    """A thin copper horizontal rule."""
    t = Table([[""]], colWidths=[170 * mm], rowHeights=[1])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, COPPER),
    ]))
    return t


# ── Content sections ─────────────────────────────────────────────
def build_story():
    ss = build_styles()
    S = []

    # Cover page is drawn via onFirstPage callback.
    # We just need a PageBreak to move to page 2.
    S.append(PageBreak())

    # Helper functions
    def h1(text):
        S.append(Paragraph(text, ss["SectionTitle"]))
        S.append(section_line())
        S.append(Spacer(1, 4 * mm))

    def h2(text):
        S.append(Paragraph(text, ss["SubTitle"]))

    def p(text):
        S.append(Paragraph(text, ss["Body"]))

    def bullet(text):
        S.append(Paragraph(f"\u2022  {text}", ss["BulletItem"]))

    def gap(h=6):
        S.append(Spacer(1, h * mm))

    # ═══════════════════════════════════════════════════════════
    # 1. SAMMENDRAG
    # ═══════════════════════════════════════════════════════════
    h1("1. Sammendrag")
    p(
        "Snyteklut AS utvikler og selger vaskbare, antibakterielle tekstilkluter "
        "spesielt designet for bruk innen rusrehabilitering og lavterskeltjenester. "
        "Produktet erstatter engangs papirlommetorklxr og gir brukerne "
        "en verdig, diskret og hygienisk losning i hverdagen."
    )
    gap()

    summary_data = [
        ["Kategori", "Detalj"],
        ["Selskap", "Snyteklut AS (under stiftelse)"],
        ["Produkt", "Vaskbar, antibakteriell tekstilklut"],
        ["Malgruppe", "Rehabiliteringssentre, LAR-program, lavterskeltjenester, kommunale rustjenester, fengselshelsetjenester"],
        ["Marked", "~400 institusjoner i Norge + nordisk ekspansjon"],
        ["Prismodell", "B2B-abonnement + enkeltkjop"],
        ["Kapitalbehov", "350 000 - 500 000 NOK"],
        ["Mal ar 1", "50 institusjoner, 1,2 MNOK omsetning"],
    ]
    S.append(styled_table(summary_data, col_widths=[4 * cm, 13 * cm]))
    gap()

    # ═══════════════════════════════════════════════════════════
    # 2. PRODUKTBESKRIVELSE
    # ═══════════════════════════════════════════════════════════
    h1("2. Produktbeskrivelse")
    p(
        "Snyteklut er en hoykvalitets tekstilklut som kombinerer funksjonalitet "
        "med verdighet. Den er utviklet i tett dialog med fagpersoner innen "
        "rusomsorgen og er tilpasset daglig bruk i krevende miljoer."
    )
    gap(3)

    h2("Materialspesifikasjoner")
    bullet("Bamboo viscose / TENCEL\u2122 70/30 blanding")
    bullet("Naturlig antibakteriell effekt fra bambus + valgfri solv-ion-behandling")
    bullet("4x mer absorberende enn bomull")
    bullet("Vaskbar ved 60\u00b0C, holder 200+ vaskesykluser")
    gap(3)

    h2("Design og format")
    bullet("Storrelse: 30 x 30 cm")
    bullet("Morke farger: gra, navy, burgunder")
    bullet("Diskret merking \u2013 intet stigmatiserende design")
    bullet("Kompakt format for lomme eller veske")
    gap()

    # ═══════════════════════════════════════════════════════════
    # 3. MARKEDSANALYSE
    # ═══════════════════════════════════════════════════════════
    h1("3. Markedsanalyse")
    p(
        "Det norske markedet for rusrehabilitering og lavterskeltjenester "
        "omfatter anslagsvis 650+ institusjoner fordelt pa flere segmenter. "
        "Tabellen under viser estimert arlig potensial."
    )
    gap()

    market_data = [
        ["Segment", "Antall", "Kluter/ar", "Pris", "Potensial"],
        ["Dognrehab", "130", "200", "89 kr", "2,3 MNOK"],
        ["Poliklinikk", "270", "50", "89 kr", "1,2 MNOK"],
        ["Kommunale tjenester", "200", "100", "89 kr", "1,8 MNOK"],
        ["Fengsel", "56", "100", "89 kr", "0,5 MNOK"],
    ]
    S.append(styled_table(market_data, col_widths=[4.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 3 * cm]))
    gap(3)

    p("<b>Totalt norsk potensial:</b> 5,8 MNOK")
    p("<b>Nordisk potensial (inkl. Sverige, Danmark, Finland):</b> ~20 MNOK")
    gap()

    # ═══════════════════════════════════════════════════════════
    # 4. PRODUKSJONSPLAN
    # ═══════════════════════════════════════════════════════════
    h1("4. Produksjonsplan")

    h2("Faseplan")
    bullet("<b>Fase 1 (0\u20136 mnd):</b> Prototyping \u2013 materialvalg, testing, brukerinnsikt")
    bullet("<b>Fase 2 (6\u201312 mnd):</b> Forste produksjon \u2013 2 000 enheter, kvalitetskontroll")
    bullet("<b>Fase 3 (12+ mnd):</b> Oppskalering \u2013 storre volum, automatisering, nordisk distribusjon")
    gap()

    # KeepTogether: heading + table stay on same page
    cost_data = [
        ["Komponent", "Kostnad (NOK)"],
        ["Stoff (bamboo/TENCEL\u2122)", "15\u201320 kr"],
        ["Sying og montering", "10\u201315 kr"],
        ["Antibakteriell behandling", "3\u20135 kr"],
        ["Emballasje", "2\u20133 kr"],
        ["Frakt per enhet", "1\u20132 kr"],
        ["Total produksjonskostnad", "31\u201345 kr"],
        ["Utsalgspris B2B", "79\u201399 kr"],
        ["Bruttomargin", "~55\u201360 %"],
    ]
    S.append(KeepTogether([
        Paragraph("Enhetskostnader", ss["SubTitle"]),
        styled_table(cost_data, col_widths=[7 * cm, 5 * cm]),
        Spacer(1, 6 * mm),
    ]))

    # ═══════════════════════════════════════════════════════════
    # 5. SALGS- OG MARKEDSSTRATEGI
    # ═══════════════════════════════════════════════════════════
    h1("5. Salgs- og markedsstrategi")

    h2("Salgskanaler")
    bullet("<b>Direkte B2B-salg:</b> Personlig oppsokende salg mot institusjonsledere og innkjopere")
    bullet("<b>Abonnementsmodell:</b> Kvartalsvis levering med rabattert pris og automatisk paafylling")
    bullet("<b>Offentlige anskaffelser:</b> Aktiv tilstedevaerelse pa Doffin.no og relevante rammeavtaler")
    bullet("<b>Fagkonferanser:</b> Stand og presentasjoner pa rustjeneste- og helsekonferanser")
    gap()

    h2("Markedsforingsbudsjett ar 1")
    mkt_data = [
        ["Aktivitet", "Budsjett"],
        ["Nettside og digital tilstedevaerelse", "25 000 kr"],
        ["Brosjyrer og produktprover", "30 000 kr"],
        ["Konferanser og messer", "25 000 kr"],
        ["Direkte oppsokende salg (reise)", "20 000 kr"],
        ["Totalt", "100 000 kr"],
    ]
    S.append(styled_table(mkt_data, col_widths=[9 * cm, 4 * cm]))
    gap()

    # ═══════════════════════════════════════════════════════════
    # 6. FINANSIERINGSPLAN
    # ═══════════════════════════════════════════════════════════
    S.append(PageBreak())
    h1("6. Finansieringsplan")

    h2("Oppstartskostnader")
    startup_data = [
        ["Post", "Belop (NOK)"],
        ["Produktutvikling og prototyping", "80 000"],
        ["Forste produksjonsserie (2 000 stk)", "90 000"],
        ["Emballasje og merking", "20 000"],
        ["Nettside og markedsforing", "40 000"],
        ["Selskapsetablering og juridisk", "15 000"],
        ["Lager og logistikk", "25 000"],
        ["Driftskapital (6 mnd buffer)", "80 000"],
        ["Totalt", "350 000"],
    ]
    S.append(styled_table(startup_data, col_widths=[9 * cm, 4 * cm]))
    gap()

    h2("Finansieringskilder")
    bullet("<b>Innovasjon Norge:</b> Oppstartsstipend / markedsavklaringsmidler")
    bullet("<b>Kommunalt naeringsfond:</b> Lokale tilskuddsordninger")
    bullet("<b>NAV:</b> Dagpenger under etablering / Grundervikar")
    bullet("<b>Egen kapital:</b> Egeninnsats og sparing")
    bullet("<b>Mikrolan:</b> Cultura Bank eller lignende")
    gap()

    # KeepTogether: P&L heading + table + break-even on same page
    pnl_data = [
        ["", "Ar 1", "Ar 2", "Ar 3"],
        ["Omsetning", "1 200 000", "2 800 000", "4 500 000"],
        ["Varekostnad (40 %)", "480 000", "1 120 000", "1 800 000"],
        ["Bruttofortjeneste", "720 000", "1 680 000", "2 700 000"],
        ["Drift og marked", "100 000", "350 000", "500 000"],
        ["Personalkostnad", "0", "200 000", "350 000"],
        ["Admin og diverse", "80 000", "120 000", "100 000"],
        ["Resultat for skatt", "540 000", "1 010 000", "1 750 000"],
    ]
    S.append(KeepTogether([
        Paragraph("Resultatprognose (3 ar)", ss["SubTitle"]),
        styled_table(pnl_data, col_widths=[5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm]),
        Spacer(1, 6 * mm),
        Paragraph("Break-even", ss["SubTitle"]),
        Paragraph("\u2022  Enheter: ~4 500 stk/ar", ss["BulletItem"]),
        Paragraph("\u2022  Institusjoner: ~37", ss["BulletItem"]),
        Paragraph("\u2022  Tidspunkt: maned 6\u20138", ss["BulletItem"]),
        Spacer(1, 6 * mm),
    ]))

    # ═══════════════════════════════════════════════════════════
    # 7. RISIKOANALYSE
    # ═══════════════════════════════════════════════════════════
    S.append(PageBreak())
    h1("7. Risikoanalyse")
    p("Nedenfor er de viktigste risikoene identifisert med sannsynlighet, konsekvens og tiltak.")
    gap()

    risk_data = [
        ["Risiko", "Sannsynlighet", "Konsekvens", "Tiltak"],
        [
            "Lav adopsjon i institusjonene",
            "Middels",
            "Hoy",
            "Gratis pilotperiode, brukerhistorier, dokumentert effekt",
        ],
        [
            "Produksjonskvalitet varierer",
            "Lav",
            "Hoy",
            "Kvalitetskontroll, flere leverandorer, sertifiseringer",
        ],
        [
            "Offentlig innkjop tar lang tid",
            "Hoy",
            "Middels",
            "Parallelt direktesalg, bygge relasjoner tidlig",
        ],
        [
            "Konkurrenter lanserer tilsvarende",
            "Lav",
            "Middels",
            "Forstegangsfordel, spesialisert merkevare, patentsok",
        ],
        [
            "Materialkostnader oker",
            "Middels",
            "Middels",
            "Langsiktige leverandoravtaler, alternativmaterialer",
        ],
        [
            "Stigma rundt malgruppe",
            "Lav",
            "Hoy",
            "Verdighetsfokus i all kommunikasjon, faglig forankring",
        ],
    ]
    S.append(styled_table(risk_data, col_widths=[4 * cm, 2.5 * cm, 2.5 * cm, 7 * cm]))
    gap()

    # ═══════════════════════════════════════════════════════════
    # 8. MILEPALSPLAN
    # ═══════════════════════════════════════════════════════════
    mile_data = [
        ["Periode", "Milepal", "Leveranser"],
        ["Mnd 1\u20132", "Selskapsetablering", "Forretningsregistrering, bankavtaler, regnskapsforer"],
        ["Mnd 2\u20134", "Produktutvikling", "Materialvalg, prototyper, brukertesting"],
        ["Mnd 4\u20136", "Pilotprogram", "3\u20135 institusjoner tester produktet, innsamling av feedback"],
        ["Mnd 6\u20138", "Forste produksjon", "2 000 enheter produsert, emballasje ferdig"],
        ["Mnd 8\u201310", "Salgsstart", "Aktiv salg til 20+ institusjoner, nettside lansert"],
        ["Mnd 10\u201312", "Evaluering ar 1", "50 institusjoner, 1,2 MNOK omsetning, break-even"],
        ["Ar 2", "Vekst", "Abonnementsmodell fullt operativ, 100+ kunder, ansettelse nr. 1"],
        ["Ar 3", "Nordisk ekspansjon", "Lansering i Sverige/Danmark, 4,5 MNOK omsetning"],
    ]
    # KeepTogether: heading + milestone table
    S.append(KeepTogether([
        Paragraph("8. Milepalsplan", ss["SectionTitle"]),
        section_line(),
        Spacer(1, 4 * mm),
        Paragraph("Oversikt over nokkelaktiviteter fra oppstart til ar 3.", ss["Body"]),
        Spacer(1, 6 * mm),
        styled_table(mile_data, col_widths=[2.8 * cm, 3.8 * cm, 9.5 * cm]),
    ]))
    gap(10)

    # ── Closing ──
    S.append(Spacer(1, 10 * mm))
    closing_style = ParagraphStyle(
        "Closing",
        fontName="Helvetica-Oblique",
        fontSize=10,
        textColor=COPPER,
        alignment=TA_CENTER,
        leading=14,
    )
    S.append(Paragraph(
        "Snyteklut \u2013 Verdighet i hverdagen",
        closing_style,
    ))

    return S


# ── Build PDF ────────────────────────────────────────────────────
def main():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        topMargin=TOP_MARGIN,
        bottomMargin=BOT_MARGIN,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        title="Snyteklut Forretningsplan 2026",
        author="Snyteklut AS",
    )

    story = build_story()

    doc.build(
        story,
        onFirstPage=draw_cover,
        onLaterPages=draw_later_pages,
    )

    print(f"PDF generated: {OUTPUT_PATH}")
    print(f"Size: {os.path.getsize(OUTPUT_PATH) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
