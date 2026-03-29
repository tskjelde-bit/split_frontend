const pptxgen = require("pptxgenjs");

const pres = new pptxgen();

// ─── Color palette ───
const C = {
  darkBg:    "1A1A2E",
  creamBg:   "F5F0EB",
  accent:    "8B5E3C",
  textLight: "F5F0EB",
  textDark:  "2D2D3A",
  highlight: "C17F59",
  accentDark:"5C3D28",
  subtle:    "D4C4B0",
};

// ─── Presentation defaults ───
pres.layout = "LAYOUT_16x9";
pres.author = "Snyteklut";
pres.subject = "Pitch Deck 2026";

// Helper: add a thin accent bar at top of slide
function addTopBar(slide, color) {
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: "100%", h: 0.06,
    fill: { color: color || C.highlight },
  });
}

// Helper: add a thin accent bar at bottom of slide
function addBottomBar(slide, color) {
  slide.addShape(pres.ShapeType.rect, {
    x: 0, y: 5.19, w: "100%", h: 0.06,
    fill: { color: color || C.highlight },
  });
}

// Helper: add slide number
function addSlideNumber(slide, num, light) {
  slide.addText(String(num).padStart(2, "0"), {
    x: 9.1, y: 5.0, w: 0.7, h: 0.35,
    fontSize: 10, fontFace: "Calibri",
    color: light ? "666680" : "9E9E9E",
    align: "right", margin: 0,
  });
}

// Helper: section title label (small top-left tag)
function addSectionTag(slide, text, light) {
  slide.addShape(pres.ShapeType.rect, {
    x: 0.5, y: 0.3, w: 1.6, h: 0.32,
    fill: { color: C.highlight },
    rectRadius: 0.05,
  });
  slide.addText(text.toUpperCase(), {
    x: 0.5, y: 0.3, w: 1.6, h: 0.32,
    fontSize: 9, fontFace: "Calibri", bold: true,
    color: "FFFFFF", align: "center", margin: 0,
    charSpacing: 2,
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.darkBg };

  // Subtle large decorative circle
  slide.addShape(pres.ShapeType.ellipse, {
    x: 6.5, y: -1.5, w: 6, h: 6,
    fill: { color: C.accent },
    transparency: 88,
  });

  // Another decorative shape
  slide.addShape(pres.ShapeType.ellipse, {
    x: -1.5, y: 3.5, w: 4, h: 4,
    fill: { color: C.highlight },
    transparency: 92,
  });

  addTopBar(slide);
  addBottomBar(slide);

  // Title
  slide.addText("Snyteklut", {
    x: 0.8, y: 1.3, w: 8, h: 1.2,
    fontSize: 54, fontFace: "Georgia", bold: true,
    color: C.textLight, margin: 0,
    charSpacing: 3,
  });

  // Decorative line under title
  slide.addShape(pres.ShapeType.rect, {
    x: 0.8, y: 2.5, w: 2.0, h: 0.04,
    fill: { color: C.highlight },
  });

  // Subtitle
  slide.addText("Verdighet i hverdagen", {
    x: 0.8, y: 2.75, w: 8, h: 0.6,
    fontSize: 24, fontFace: "Georgia", italic: true,
    color: C.highlight, margin: 0,
  });

  // Year label
  slide.addText("Forretningsplan 2026", {
    x: 0.8, y: 3.6, w: 8, h: 0.4,
    fontSize: 14, fontFace: "Calibri",
    color: C.subtle, margin: 0,
    charSpacing: 4,
  });

  // Small tagline at bottom
  slide.addText("Spesialisert hygieneproduksjon for rusrehabiliteringsinstitusjoner", {
    x: 0.8, y: 4.5, w: 7, h: 0.35,
    fontSize: 11, fontFace: "Calibri",
    color: "666680", margin: 0,
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 2 — PROBLEMET
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.creamBg };

  addTopBar(slide, C.accent);
  addBottomBar(slide, C.accent);
  addSectionTag(slide, "Problemet");
  addSlideNumber(slide, 2, false);

  // Section title
  slide.addText("Et usynlig problem", {
    x: 0.5, y: 0.8, w: 5, h: 0.6,
    fontSize: 30, fontFace: "Georgia", bold: true,
    color: C.textDark, margin: 0,
  });

  // Left column — problem description
  const problemTexts = [
    { text: "Pasienter i rusrehabilitering med nasal substansbruk sliter med kroniske neseblødninger og nasal utflod.", options: { fontSize: 13, fontFace: "Calibri", color: C.textDark, breakLine: true, paraSpaceAfter: 8 } },
    { text: "", options: { fontSize: 6, breakLine: true } },
    { text: "Papirtørkler løser seg opp i kontakt med blod", options: { fontSize: 12, fontFace: "Calibri", color: C.textDark, bullet: true, breakLine: true, paraSpaceAfter: 4 } },
    { text: "Vanlige kluter mangler antibakteriell beskyttelse", options: { fontSize: 12, fontFace: "Calibri", color: C.textDark, bullet: true, breakLine: true, paraSpaceAfter: 4 } },
    { text: "Gjentatt bruk av uegnede produkter forverrer skader", options: { fontSize: 12, fontFace: "Calibri", color: C.textDark, bullet: true, breakLine: true, paraSpaceAfter: 4 } },
    { text: "Ingen eksisterende produkter er utviklet for dette behovet", options: { fontSize: 12, fontFace: "Calibri", color: C.textDark, bullet: true, breakLine: true } },
  ];
  slide.addText(problemTexts, {
    x: 0.5, y: 1.6, w: 4.8, h: 2.8, valign: "top", margin: 0,
  });

  // Right side — big stat card
  slide.addShape(pres.ShapeType.roundRect, {
    x: 5.8, y: 1.0, w: 3.8, h: 3.6,
    fill: { color: C.darkBg },
    rectRadius: 0.15,
    shadow: { type: "outer", blur: 12, offset: 4, color: "000000", opacity: 0.15 },
  });

  slide.addText("400+", {
    x: 5.8, y: 1.4, w: 3.8, h: 1.2,
    fontSize: 68, fontFace: "Georgia", bold: true,
    color: C.highlight, align: "center", margin: 0,
  });

  slide.addText("institusjoner i Norge", {
    x: 5.8, y: 2.6, w: 3.8, h: 0.4,
    fontSize: 16, fontFace: "Georgia",
    color: C.textLight, align: "center", margin: 0,
  });

  slide.addShape(pres.ShapeType.rect, {
    x: 6.8, y: 3.15, w: 1.8, h: 0.03,
    fill: { color: C.highlight },
  });

  slide.addText("mangler spesialiserte\nhygieneprodukter for\nnasal rehabilitering", {
    x: 5.8, y: 3.3, w: 3.8, h: 1.0,
    fontSize: 11, fontFace: "Calibri",
    color: C.subtle, align: "center", margin: 0,
    lineSpacingMultiple: 1.3,
  });

  // Bottom accent quote
  slide.addShape(pres.ShapeType.rect, {
    x: 0.5, y: 4.6, w: 0.04, h: 0.5,
    fill: { color: C.highlight },
  });
  slide.addText("\"Det finnes ingen verdige alternativer for pasienter som blør fra nesen daglig.\"", {
    x: 0.75, y: 4.6, w: 4.5, h: 0.5,
    fontSize: 11, fontFace: "Georgia", italic: true,
    color: C.accent, margin: 0,
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 3 — LOSNINGEN
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.darkBg };

  addTopBar(slide);
  addBottomBar(slide);
  addSectionTag(slide, "Losningen");
  addSlideNumber(slide, 3, true);

  // Title
  slide.addText("Snyteklut", {
    x: 0.5, y: 0.8, w: 9, h: 0.6,
    fontSize: 30, fontFace: "Georgia", bold: true,
    color: C.textLight, margin: 0,
  });
  slide.addText("Spesialutviklet for verdighet og funksjon", {
    x: 0.5, y: 1.35, w: 9, h: 0.35,
    fontSize: 13, fontFace: "Calibri",
    color: C.subtle, margin: 0,
  });

  // Product spec cards (2 rows x 3 columns, but 5 cards)
  const specs = [
    { icon: "\u2727", title: "Bambusviskose / TENCEL\u2122", desc: "70/30 blanding for optimal mykhet og holdbarhet" },
    { icon: "\u2694", title: "Antibakteriell", desc: "Naturlig antibakteriell effekt fra bambusfiber" },
    { icon: "\u267B", title: "200+ vask ved 60\u00B0C", desc: "Industriell vaskbar uten kvalitetstap" },
    { icon: "\u25C8", title: "4\u00D7 mer absorberende", desc: "Enn tradisjonell bomull, h\u00E5ndterer blod og slim" },
    { icon: "\u25A0", title: "M\u00F8rke farger", desc: "Skjuler blodflekker \u2014 reduserer stigma" },
  ];

  const cardW = 2.7;
  const cardH = 1.35;
  const gap = 0.25;
  const startX = 0.5;
  const row1Y = 1.95;
  const row2Y = row1Y + cardH + gap;

  specs.forEach((spec, i) => {
    const col = i < 3 ? i : i - 3;
    const row = i < 3 ? 0 : 1;
    const cx = startX + col * (cardW + gap);
    const cy = row === 0 ? row1Y : row2Y;

    // Card background
    slide.addShape(pres.ShapeType.roundRect, {
      x: cx, y: cy, w: cardW, h: cardH,
      fill: { color: "2D2D3A" },
      rectRadius: 0.1,
      line: { color: C.accent, width: 0.75 },
    });

    // Icon circle
    slide.addShape(pres.ShapeType.ellipse, {
      x: cx + 0.15, y: cy + 0.15, w: 0.45, h: 0.45,
      fill: { color: C.highlight },
      transparency: 70,
    });

    // Title
    slide.addText(spec.title, {
      x: cx + 0.15, y: cy + 0.7, w: cardW - 0.3, h: 0.3,
      fontSize: 12, fontFace: "Calibri", bold: true,
      color: C.highlight, margin: 0,
    });

    // Description
    slide.addText(spec.desc, {
      x: cx + 0.15, y: cy + 0.95, w: cardW - 0.3, h: 0.35,
      fontSize: 10, fontFace: "Calibri",
      color: C.subtle, margin: 0,
      lineSpacingMultiple: 1.2,
    });
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 4 — MARKEDET
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.creamBg };

  addTopBar(slide, C.accent);
  addBottomBar(slide, C.accent);
  addSectionTag(slide, "Markedet");
  addSlideNumber(slide, 4, false);

  // Title
  slide.addText("Markedsmulighet", {
    x: 0.5, y: 0.8, w: 5, h: 0.6,
    fontSize: 30, fontFace: "Georgia", bold: true,
    color: C.textDark, margin: 0,
  });

  // Market size callouts — two boxes side by side
  // Norway
  slide.addShape(pres.ShapeType.roundRect, {
    x: 0.5, y: 1.55, w: 2.8, h: 1.5,
    fill: { color: C.darkBg },
    rectRadius: 0.1,
  });
  slide.addText("5.8", {
    x: 0.5, y: 1.6, w: 2.8, h: 0.8,
    fontSize: 48, fontFace: "Georgia", bold: true,
    color: C.highlight, align: "center", margin: 0,
  });
  slide.addText("MNOK \u2014 Norge", {
    x: 0.5, y: 2.35, w: 2.8, h: 0.3,
    fontSize: 13, fontFace: "Calibri",
    color: C.subtle, align: "center", margin: 0,
  });
  slide.addText("Estimert markedsverdi", {
    x: 0.5, y: 2.65, w: 2.8, h: 0.25,
    fontSize: 9, fontFace: "Calibri",
    color: "666680", align: "center", margin: 0,
  });

  // Nordics
  slide.addShape(pres.ShapeType.roundRect, {
    x: 3.55, y: 1.55, w: 2.8, h: 1.5,
    fill: { color: C.accent },
    rectRadius: 0.1,
  });
  slide.addText("20", {
    x: 3.55, y: 1.6, w: 2.8, h: 0.8,
    fontSize: 48, fontFace: "Georgia", bold: true,
    color: "FFFFFF", align: "center", margin: 0,
  });
  slide.addText("MNOK \u2014 Norden", {
    x: 3.55, y: 2.35, w: 2.8, h: 0.3,
    fontSize: 13, fontFace: "Calibri",
    color: C.creamBg, align: "center", margin: 0,
  });
  slide.addText("Ekspansjonsm\u00E5l \u00E5r 3", {
    x: 3.55, y: 2.65, w: 2.8, h: 0.25,
    fontSize: 9, fontFace: "Calibri",
    color: "D4A97A", align: "center", margin: 0,
  });

  // Bar chart — segment breakdown (manual bars)
  const segments = [
    { label: "D\u00F8gnrehab", value: 130, max: 270 },
    { label: "Poliklinikker", value: 270, max: 270 },
    { label: "Kommunale", value: 200, max: 270 },
    { label: "Fengsler", value: 56, max: 270 },
  ];

  const chartX = 0.5;
  const chartY = 3.4;
  const chartW = 6.0;
  const barH = 0.28;
  const barGap = 0.15;
  const maxBarW = 4.0;
  const labelW = 1.5;

  // Chart title
  slide.addText("Segmenter (antall institusjoner)", {
    x: chartX, y: chartY - 0.35, w: chartW, h: 0.3,
    fontSize: 11, fontFace: "Calibri", bold: true,
    color: C.textDark, margin: 0,
  });

  segments.forEach((seg, i) => {
    const by = chartY + i * (barH + barGap);
    const bw = (seg.value / seg.max) * maxBarW;

    // Label
    slide.addText(seg.label, {
      x: chartX, y: by, w: labelW, h: barH,
      fontSize: 10, fontFace: "Calibri",
      color: C.textDark, align: "right", margin: 0,
      valign: "middle",
    });

    // Bar background
    slide.addShape(pres.ShapeType.roundRect, {
      x: chartX + labelW + 0.15, y: by + 0.04, w: maxBarW, h: barH - 0.08,
      fill: { color: C.subtle },
      transparency: 50,
      rectRadius: 0.04,
    });

    // Bar fill
    slide.addShape(pres.ShapeType.roundRect, {
      x: chartX + labelW + 0.15, y: by + 0.04, w: bw, h: barH - 0.08,
      fill: { color: i % 2 === 0 ? C.accent : C.highlight },
      rectRadius: 0.04,
    });

    // Value label
    slide.addText(String(seg.value), {
      x: chartX + labelW + 0.15 + bw + 0.1, y: by, w: 0.5, h: barH,
      fontSize: 11, fontFace: "Calibri", bold: true,
      color: C.textDark, margin: 0, valign: "middle",
    });
  });

  // Right side — summary card
  slide.addShape(pres.ShapeType.roundRect, {
    x: 7.0, y: 1.55, w: 2.6, h: 3.4,
    fill: { color: "FFFFFF" },
    rectRadius: 0.1,
    shadow: { type: "outer", blur: 8, offset: 3, color: "000000", opacity: 0.08 },
  });

  slide.addText("Totalt", {
    x: 7.0, y: 1.7, w: 2.6, h: 0.3,
    fontSize: 11, fontFace: "Calibri",
    color: C.accent, align: "center", margin: 0,
    charSpacing: 3,
  });

  slide.addText("656", {
    x: 7.0, y: 2.0, w: 2.6, h: 0.8,
    fontSize: 52, fontFace: "Georgia", bold: true,
    color: C.textDark, align: "center", margin: 0,
  });

  slide.addText("institusjoner", {
    x: 7.0, y: 2.7, w: 2.6, h: 0.3,
    fontSize: 13, fontFace: "Calibri",
    color: C.accent, align: "center", margin: 0,
  });

  slide.addShape(pres.ShapeType.rect, {
    x: 7.5, y: 3.1, w: 1.6, h: 0.02,
    fill: { color: C.subtle },
  });

  slide.addText([
    { text: "B2B-marked", options: { fontSize: 10, fontFace: "Calibri", color: C.textDark, breakLine: true, paraSpaceAfter: 3 } },
    { text: "Offentlige anbud", options: { fontSize: 10, fontFace: "Calibri", color: C.textDark, breakLine: true, paraSpaceAfter: 3 } },
    { text: "Abonnement", options: { fontSize: 10, fontFace: "Calibri", color: C.textDark, breakLine: true } },
  ], {
    x: 7.2, y: 3.3, w: 2.2, h: 1.4,
    align: "center", margin: 0, valign: "top",
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 5 — FORRETNINGSMODELL
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.darkBg };

  addTopBar(slide);
  addBottomBar(slide);
  addSectionTag(slide, "Modell");
  addSlideNumber(slide, 5, true);

  // Title
  slide.addText("Forretningsmodell", {
    x: 0.5, y: 0.8, w: 9, h: 0.6,
    fontSize: 30, fontFace: "Georgia", bold: true,
    color: C.textLight, margin: 0,
  });

  // Three model pillars
  const pillars = [
    { title: "B2B Direktesalg", desc: "Direkte til institusjoner via etablerte innkjopskanaler og personlig salg" },
    { title: "Abonnement", desc: "Kvartalsvis levering sikrer forutsigbar inntekt og kundelojalitet" },
    { title: "Offentlige anbud", desc: "Registrert pa Doffin for offentlige anskaffelser og rammeavtaler" },
  ];

  pillars.forEach((p, i) => {
    const px = 0.5 + i * 3.05;
    const py = 1.65;

    // Pillar card
    slide.addShape(pres.ShapeType.roundRect, {
      x: px, y: py, w: 2.8, h: 1.8,
      fill: { color: "2D2D3A" },
      rectRadius: 0.1,
      line: { color: C.accent, width: 0.5 },
    });

    // Number circle
    slide.addShape(pres.ShapeType.ellipse, {
      x: px + 1.1, y: py + 0.15, w: 0.6, h: 0.6,
      fill: { color: C.highlight },
    });
    slide.addText(String(i + 1), {
      x: px + 1.1, y: py + 0.15, w: 0.6, h: 0.6,
      fontSize: 18, fontFace: "Georgia", bold: true,
      color: "FFFFFF", align: "center", valign: "middle", margin: 0,
    });

    // Title
    slide.addText(p.title, {
      x: px + 0.15, y: py + 0.85, w: 2.5, h: 0.3,
      fontSize: 13, fontFace: "Calibri", bold: true,
      color: C.highlight, align: "center", margin: 0,
    });

    // Description
    slide.addText(p.desc, {
      x: px + 0.15, y: py + 1.15, w: 2.5, h: 0.55,
      fontSize: 10, fontFace: "Calibri",
      color: C.subtle, align: "center", margin: 0,
      lineSpacingMultiple: 1.3,
    });
  });

  // Unit economics — large bottom section
  slide.addShape(pres.ShapeType.roundRect, {
    x: 0.5, y: 3.75, w: 9.0, h: 1.25,
    fill: { color: C.accent },
    rectRadius: 0.1,
  });

  slide.addText("Enhetsokonomi", {
    x: 0.7, y: 3.82, w: 2, h: 0.3,
    fontSize: 10, fontFace: "Calibri", bold: true,
    color: "FFFFFF", margin: 0, charSpacing: 2,
  });

  // Cost → Price → Margin flow
  const econItems = [
    { label: "Kostnad", value: "40 kr", sub: "per enhet" },
    { label: "Salgspris", value: "80 kr", sub: "per enhet" },
    { label: "Bruttomargin", value: "50%", sub: "per enhet" },
  ];

  econItems.forEach((item, i) => {
    const ex = 1.0 + i * 2.8;
    const ey = 4.1;

    slide.addText(item.value, {
      x: ex, y: ey, w: 2.0, h: 0.5,
      fontSize: 32, fontFace: "Georgia", bold: true,
      color: "FFFFFF", align: "center", margin: 0,
    });
    slide.addText(item.label, {
      x: ex, y: ey + 0.5, w: 2.0, h: 0.25,
      fontSize: 10, fontFace: "Calibri",
      color: C.creamBg, align: "center", margin: 0,
    });

    // Arrow between items
    if (i < 2) {
      slide.addText("\u2192", {
        x: ex + 2.0, y: ey + 0.05, w: 0.6, h: 0.45,
        fontSize: 24, fontFace: "Calibri",
        color: C.creamBg, align: "center", margin: 0,
        transparency: 40,
      });
    }
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 6 — OKONOMI
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.creamBg };

  addTopBar(slide, C.accent);
  addBottomBar(slide, C.accent);
  addSectionTag(slide, "Okonomi");
  addSlideNumber(slide, 6, false);

  // Title
  slide.addText("Finansielle fremskrivninger", {
    x: 0.5, y: 0.8, w: 6, h: 0.6,
    fontSize: 30, fontFace: "Georgia", bold: true,
    color: C.textDark, margin: 0,
  });

  // Revenue projection chart (manual bar chart — 3 years)
  const years = [
    { label: "Ar 1", value: 1.2, display: "1.2M" },
    { label: "Ar 2", value: 2.8, display: "2.8M" },
    { label: "Ar 3", value: 4.5, display: "4.5M" },
  ];

  const chartBaseX = 0.8;
  const chartBaseY = 4.35;
  const colW = 1.6;
  const colGap = 0.6;
  const maxH = 2.6;
  const maxVal = 5.0;

  // Chart area background
  slide.addShape(pres.ShapeType.roundRect, {
    x: 0.5, y: 1.55, w: 6.2, h: 3.35,
    fill: { color: "FFFFFF" },
    rectRadius: 0.1,
    shadow: { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.06 },
  });

  // Grid lines
  for (let g = 0; g <= 4; g++) {
    const gy = chartBaseY - (g / 4) * maxH;
    slide.addShape(pres.ShapeType.rect, {
      x: 0.7, y: gy, w: 5.8, h: 0.01,
      fill: { color: C.subtle },
      transparency: 60,
    });
    slide.addText(String(g * 1.25) + "M", {
      x: 0.2, y: gy - 0.12, w: 0.5, h: 0.24,
      fontSize: 8, fontFace: "Calibri",
      color: "999999", align: "right", margin: 0,
    });
  }

  years.forEach((yr, i) => {
    const bx = chartBaseX + i * (colW + colGap);
    const bh = (yr.value / maxVal) * maxH;
    const by = chartBaseY - bh;

    // Bar
    slide.addShape(pres.ShapeType.roundRect, {
      x: bx, y: by, w: colW, h: bh,
      fill: { color: i === 2 ? C.highlight : C.accent },
      rectRadius: 0.06,
    });

    // Value on top of bar
    slide.addText(yr.display, {
      x: bx, y: by - 0.35, w: colW, h: 0.3,
      fontSize: 18, fontFace: "Georgia", bold: true,
      color: C.textDark, align: "center", margin: 0,
    });

    // Year label below bar
    slide.addText(yr.label, {
      x: bx, y: chartBaseY + 0.08, w: colW, h: 0.25,
      fontSize: 11, fontFace: "Calibri", bold: true,
      color: C.textDark, align: "center", margin: 0,
    });
  });

  // Right side — key numbers
  slide.addShape(pres.ShapeType.roundRect, {
    x: 7.1, y: 1.55, w: 2.5, h: 3.35,
    fill: { color: C.darkBg },
    rectRadius: 0.1,
  });

  slide.addText("Nokkeltal", {
    x: 7.1, y: 1.7, w: 2.5, h: 0.3,
    fontSize: 10, fontFace: "Calibri", bold: true,
    color: C.highlight, align: "center", margin: 0,
    charSpacing: 3,
  });

  const keyNums = [
    { val: "350K", label: "Oppstartskostnad" },
    { val: "6-8", label: "Mnd til breakeven" },
    { val: "540K", label: "Overskudd ar 1" },
    { val: "50%", label: "Bruttomargin" },
  ];

  keyNums.forEach((kn, i) => {
    const ky = 2.15 + i * 0.7;

    slide.addText(kn.val, {
      x: 7.3, y: ky, w: 2.1, h: 0.35,
      fontSize: 22, fontFace: "Georgia", bold: true,
      color: C.highlight, align: "center", margin: 0,
    });
    slide.addText(kn.label, {
      x: 7.3, y: ky + 0.32, w: 2.1, h: 0.2,
      fontSize: 9, fontFace: "Calibri",
      color: C.subtle, align: "center", margin: 0,
    });

    if (i < 3) {
      slide.addShape(pres.ShapeType.rect, {
        x: 7.6, y: ky + 0.58, w: 1.4, h: 0.01,
        fill: { color: C.accent },
        transparency: 60,
      });
    }
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 7 — KONKURRANSEFORTRINN
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.darkBg };

  addTopBar(slide);
  addBottomBar(slide);
  addSectionTag(slide, "Fortrinn");
  addSlideNumber(slide, 7, true);

  // Large background decorative shape
  slide.addShape(pres.ShapeType.ellipse, {
    x: 7, y: 0.5, w: 5, h: 5,
    fill: { color: C.accent },
    transparency: 92,
  });

  // Title
  slide.addText("Konkurransefortrinn", {
    x: 0.5, y: 0.8, w: 9, h: 0.6,
    fontSize: 30, fontFace: "Georgia", bold: true,
    color: C.textLight, margin: 0,
  });

  slide.addText("Ingen direkte konkurrenter i markedet", {
    x: 0.5, y: 1.4, w: 9, h: 0.35,
    fontSize: 14, fontFace: "Calibri", italic: true,
    color: C.highlight, margin: 0,
  });

  // Four advantage cards in 2x2 grid
  const advantages = [
    { num: "01", title: "Forst i markedet", desc: "Ingen eksisterende produkter er spesialdesignet for nasal rehabilitering i rusomsorg" },
    { num: "02", title: "Klinisk opprinnelse", desc: "Utviklet fra reell klinisk erfaring ved Kilevangen bo og rehabilitering" },
    { num: "03", title: "Unik posisjon", desc: "Eneste produkt som kombinerer antibakteriell, vaskbar og hudvennlig teknologi for dette formalet" },
    { num: "04", title: "Faglig nettverk", desc: "Sterk tilknytning til rehabiliteringsfeltet gir troverdighet og distribusjonskanaler" },
  ];

  advantages.forEach((adv, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const ax = 0.5 + col * 4.55;
    const ay = 2.0 + row * 1.5;

    // Card
    slide.addShape(pres.ShapeType.roundRect, {
      x: ax, y: ay, w: 4.3, h: 1.25,
      fill: { color: "2D2D3A" },
      rectRadius: 0.08,
      line: { color: C.accent, width: 0.5 },
    });

    // Number
    slide.addText(adv.num, {
      x: ax + 0.15, y: ay + 0.12, w: 0.6, h: 0.45,
      fontSize: 28, fontFace: "Georgia", bold: true,
      color: C.highlight, margin: 0,
    });

    // Title
    slide.addText(adv.title, {
      x: ax + 0.8, y: ay + 0.15, w: 3.3, h: 0.3,
      fontSize: 14, fontFace: "Calibri", bold: true,
      color: C.textLight, margin: 0,
    });

    // Description
    slide.addText(adv.desc, {
      x: ax + 0.8, y: ay + 0.5, w: 3.3, h: 0.65,
      fontSize: 10, fontFace: "Calibri",
      color: C.subtle, margin: 0,
      lineSpacingMultiple: 1.3,
    });
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 8 — MILEPALER
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.creamBg };

  addTopBar(slide, C.accent);
  addBottomBar(slide, C.accent);
  addSectionTag(slide, "Milepaler");
  addSlideNumber(slide, 8, false);

  // Title
  slide.addText("Milepaler og tidslinje", {
    x: 0.5, y: 0.8, w: 9, h: 0.6,
    fontSize: 30, fontFace: "Georgia", bold: true,
    color: C.textDark, margin: 0,
  });

  // Timeline — horizontal line
  const lineY = 2.6;
  slide.addShape(pres.ShapeType.rect, {
    x: 0.5, y: lineY, w: 9.0, h: 0.04,
    fill: { color: C.accent },
  });

  // Timeline milestones
  const milestones = [
    { x: 1.0, label: "Mnd 1\u20132", title: "Prototyping", desc: "Materialvalg, testing, design", above: true },
    { x: 3.0, label: "Mnd 3\u20134", title: "Pilottest", desc: "Testing ved Kilevangen", above: false },
    { x: 5.0, label: "Mnd 5\u20136", title: "Produksjon", desc: "Produksjonsstart med leverandor", above: true },
    { x: 7.0, label: "Mnd 6\u20138", title: "Lansering", desc: "Salgsstart og markedsforing", above: false },
    { x: 9.0, label: "Ar 2\u20133", title: "Skalering", desc: "Nordisk ekspansjon", above: true },
  ];

  milestones.forEach((ms) => {
    // Dot on timeline
    slide.addShape(pres.ShapeType.ellipse, {
      x: ms.x - 0.15, y: lineY - 0.13, w: 0.3, h: 0.3,
      fill: { color: C.highlight },
    });

    if (ms.above) {
      // Card above
      slide.addShape(pres.ShapeType.roundRect, {
        x: ms.x - 0.65, y: lineY - 1.65, w: 1.5, h: 1.35,
        fill: { color: "FFFFFF" },
        rectRadius: 0.08,
        shadow: { type: "outer", blur: 5, offset: 2, color: "000000", opacity: 0.06 },
      });

      slide.addText(ms.label, {
        x: ms.x - 0.65, y: lineY - 1.55, w: 1.5, h: 0.25,
        fontSize: 9, fontFace: "Calibri", bold: true,
        color: C.highlight, align: "center", margin: 0,
        charSpacing: 1,
      });

      slide.addText(ms.title, {
        x: ms.x - 0.65, y: lineY - 1.25, w: 1.5, h: 0.3,
        fontSize: 12, fontFace: "Georgia", bold: true,
        color: C.textDark, align: "center", margin: 0,
      });

      slide.addText(ms.desc, {
        x: ms.x - 0.55, y: lineY - 0.95, w: 1.3, h: 0.5,
        fontSize: 9, fontFace: "Calibri",
        color: "777777", align: "center", margin: 0,
        lineSpacingMultiple: 1.3,
      });

      // Connector line
      slide.addShape(pres.ShapeType.rect, {
        x: ms.x - 0.01, y: lineY - 0.3, w: 0.02, h: 0.3,
        fill: { color: C.subtle },
      });
    } else {
      // Card below
      slide.addShape(pres.ShapeType.roundRect, {
        x: ms.x - 0.65, y: lineY + 0.45, w: 1.5, h: 1.35,
        fill: { color: "FFFFFF" },
        rectRadius: 0.08,
        shadow: { type: "outer", blur: 5, offset: 2, color: "000000", opacity: 0.06 },
      });

      slide.addText(ms.label, {
        x: ms.x - 0.65, y: lineY + 0.55, w: 1.5, h: 0.25,
        fontSize: 9, fontFace: "Calibri", bold: true,
        color: C.highlight, align: "center", margin: 0,
        charSpacing: 1,
      });

      slide.addText(ms.title, {
        x: ms.x - 0.65, y: lineY + 0.8, w: 1.5, h: 0.3,
        fontSize: 12, fontFace: "Georgia", bold: true,
        color: C.textDark, align: "center", margin: 0,
      });

      slide.addText(ms.desc, {
        x: ms.x - 0.55, y: lineY + 1.1, w: 1.3, h: 0.5,
        fontSize: 9, fontFace: "Calibri",
        color: "777777", align: "center", margin: 0,
        lineSpacingMultiple: 1.3,
      });

      // Connector line
      slide.addShape(pres.ShapeType.rect, {
        x: ms.x - 0.01, y: lineY + 0.04, w: 0.02, h: 0.4,
        fill: { color: C.subtle },
      });
    }
  });

  // Progress indicator bar
  slide.addShape(pres.ShapeType.roundRect, {
    x: 0.5, y: 4.65, w: 9.0, h: 0.3,
    fill: { color: C.subtle },
    transparency: 50,
    rectRadius: 0.06,
  });
  slide.addShape(pres.ShapeType.roundRect, {
    x: 0.5, y: 4.65, w: 1.8, h: 0.3,
    fill: { color: C.highlight },
    rectRadius: 0.06,
  });
  slide.addText("Vi er her", {
    x: 0.5, y: 4.65, w: 1.8, h: 0.3,
    fontSize: 9, fontFace: "Calibri", bold: true,
    color: "FFFFFF", align: "center", valign: "middle", margin: 0,
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 9 — TEAMET
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.darkBg };

  // Large decorative shapes
  slide.addShape(pres.ShapeType.ellipse, {
    x: -2, y: -2, w: 7, h: 7,
    fill: { color: C.accent },
    transparency: 93,
  });

  addTopBar(slide);
  addBottomBar(slide);
  addSectionTag(slide, "Teamet");
  addSlideNumber(slide, 9, true);

  // Title
  slide.addText("Bak Snyteklut", {
    x: 0.5, y: 0.8, w: 9, h: 0.6,
    fontSize: 30, fontFace: "Georgia", bold: true,
    color: C.textLight, margin: 0,
  });

  slide.addText("Utviklet av de som kjenner behovet best", {
    x: 0.5, y: 1.35, w: 9, h: 0.35,
    fontSize: 13, fontFace: "Calibri", italic: true,
    color: C.subtle, margin: 0,
  });

  // Central large card
  slide.addShape(pres.ShapeType.roundRect, {
    x: 1.5, y: 1.9, w: 7.0, h: 2.8,
    fill: { color: "2D2D3A" },
    rectRadius: 0.12,
    line: { color: C.accent, width: 0.75 },
  });

  // Team attributes — 4 quadrants inside the card
  const teamAttrs = [
    { title: "Klinisk erfaring", desc: "Utviklet ved Kilevangen bo og rehabilitering med forstehandserfaring fra daglig pasientkontakt", icon: "\u2605" },
    { title: "Pasientinnsikt", desc: "Direkte forstaelse av pasienters behov, utfordringer og verdighetsopplevelse", icon: "\u2665" },
    { title: "Faglig nettverk", desc: "Profesjonelt nettverk i rehabiliteringsfeltet gir tilgang til beslutningstagere", icon: "\u2726" },
    { title: "Troverdighet", desc: "Praktisk bakgrunn gir unik troverdighet hos innkjopere og klinisk personell", icon: "\u2713" },
  ];

  teamAttrs.forEach((attr, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const tx = 1.8 + col * 3.4;
    const ty = 2.1 + row * 1.3;

    // Accent line left of each item
    slide.addShape(pres.ShapeType.rect, {
      x: tx, y: ty, w: 0.04, h: 0.9,
      fill: { color: C.highlight },
    });

    slide.addText(attr.title, {
      x: tx + 0.2, y: ty, w: 3.0, h: 0.3,
      fontSize: 14, fontFace: "Georgia", bold: true,
      color: C.highlight, margin: 0,
    });

    slide.addText(attr.desc, {
      x: tx + 0.2, y: ty + 0.35, w: 3.0, h: 0.55,
      fontSize: 10, fontFace: "Calibri",
      color: C.subtle, margin: 0,
      lineSpacingMultiple: 1.3,
    });
  });
}


// ═══════════════════════════════════════════════════
// SLIDE 10 — KONTAKT
// ═══════════════════════════════════════════════════
{
  const slide = pres.addSlide();
  slide.background = { fill: C.darkBg };

  // Large decorative gradient-like shapes
  slide.addShape(pres.ShapeType.ellipse, {
    x: 3, y: -1, w: 8, h: 8,
    fill: { color: C.accent },
    transparency: 90,
  });
  slide.addShape(pres.ShapeType.ellipse, {
    x: -3, y: 2, w: 6, h: 6,
    fill: { color: C.highlight },
    transparency: 93,
  });

  addTopBar(slide);
  addBottomBar(slide);

  // Main heading
  slide.addText("La oss snakke", {
    x: 0.5, y: 1.0, w: 9.0, h: 0.8,
    fontSize: 42, fontFace: "Georgia", bold: true,
    color: C.textLight, align: "center", margin: 0,
  });

  // Subtitle
  slide.addText("Klar for a gjore en forskjell?", {
    x: 0.5, y: 1.85, w: 9.0, h: 0.5,
    fontSize: 18, fontFace: "Georgia", italic: true,
    color: C.highlight, align: "center", margin: 0,
  });

  // Decorative line
  slide.addShape(pres.ShapeType.rect, {
    x: 4.0, y: 2.55, w: 2.0, h: 0.03,
    fill: { color: C.highlight },
  });

  // Contact info card
  slide.addShape(pres.ShapeType.roundRect, {
    x: 2.5, y: 2.85, w: 5.0, h: 1.4,
    fill: { color: "2D2D3A" },
    rectRadius: 0.1,
    line: { color: C.accent, width: 0.75 },
  });

  slide.addText([
    { text: "E-post:  kontakt@snyteklut.no", options: { fontSize: 13, fontFace: "Calibri", color: C.textLight, breakLine: true, paraSpaceAfter: 6 } },
    { text: "Telefon:  +47 XXX XX XXX", options: { fontSize: 13, fontFace: "Calibri", color: C.textLight, breakLine: true, paraSpaceAfter: 6 } },
    { text: "Web:  www.snyteklut.no", options: { fontSize: 13, fontFace: "Calibri", color: C.highlight, breakLine: true } },
  ], {
    x: 3.0, y: 2.95, w: 4.0, h: 1.2, valign: "middle", margin: 0,
  });

  // CTA button
  slide.addShape(pres.ShapeType.roundRect, {
    x: 3.2, y: 4.5, w: 3.6, h: 0.55,
    fill: { color: C.highlight },
    rectRadius: 0.08,
    shadow: { type: "outer", blur: 8, offset: 3, color: "000000", opacity: 0.2 },
  });

  slide.addText("Bestill provepakke", {
    x: 3.2, y: 4.5, w: 3.6, h: 0.55,
    fontSize: 16, fontFace: "Calibri", bold: true,
    color: "FFFFFF", align: "center", valign: "middle", margin: 0,
    charSpacing: 2,
  });
}


// ─── Generate the file ───
const outputPath = "/Users/torbjorntest/WWW/snyteklut/Snyteklut_Pitch.pptx";
pres.writeFile({ fileName: outputPath })
  .then(() => console.log("Pitch deck created at: " + outputPath))
  .catch((err) => console.error("Error:", err));
