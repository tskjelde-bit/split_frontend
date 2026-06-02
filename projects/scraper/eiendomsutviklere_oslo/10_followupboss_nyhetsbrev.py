#!/usr/bin/env python3
"""
10_followupboss_nyhetsbrev.py — Vasket mottakerliste for nybygg-nyhetsbrevet, klar
for import til FollowUpBoss.

Formål (forskjellig fra 6_vasket_epost.py som er off-market-utsendelse for BFG8):
  Torbjørn sender nyhetsbrevet om nyboligmarkedet til eiendomsutviklere i Oslo. Vi vil
  treffe SMÅ/MID nybygg- og bygård-utviklere (potensielle megleroppdrag) og luke ut
  STORE sluggere (OBOS, Bane NOR, Veidekke …) som bygger hundrevis av boliger og har
  eget meglerteam.

Strategi (avklart med bruker — "hybrid"):
  1. Mekanisk filter: blokkliste (store navn) + selger-blokk + krav om ekte e-post.
  2. Gråsone (omsetning >= 30 mill ELLER ansatte >= 10) rutes til research-verdikt i
     output/nyhetsbrev_relevans.json. Alt under terskelen = auto-keep (= målgruppen).
     Viktig: høy omsetning ALENE kutter ikke — en én-prosjekt-bygård-SPV bokfører
     salgsåret høyt og er nettopp en kunde. Research skiller SPV fra operativ storutvikler.
  3. E-postvalg: person-e-post FØRST (DL-proxy via navn-match), rolle-innboks kun hvis
     ingen person-e-post finnes. Primær + opptil 2 ekstra navngitte personer (maks 3/selskap).
  4. Aktør-dedup (samme DL / SPV-cluster → én mottaker) + global adresse-dedup.

Output (idempotent, re-kjørbart):
  output/followupboss-nyhetsbrev.csv  — import-fil til FollowUpBoss
  output/nyhetsbrev-review.html       — frittstående review (hvem inn/ut + research-grunner)
  output/nyhetsbrev_grayzone.json     — gråsone-kandidater (input til research-passet)
  output/nyhetsbrev_relevans.json     — research-verdikt per orgnr (hand-redigerbar override)

FollowUpBoss-import: last opp CSV-en i FUB → People → Import. Kolonne-mapping:
  First Name→First Name, Last Name→Last Name, Email→Email, Phone→Phone, Company→Company,
  Tags→Tags, Source→Source, Address→Address, City→City, Zip→Zip, Background→Background.

BRUK:
  python 10_followupboss_nyhetsbrev.py
  # Mangler nyhetsbrev_relevans.json behandles hele gråsonen som keep (med advarsel).
  # Rediger blokkliste_store_utviklere.json / nyhetsbrev_relevans.json og kjør på nytt.
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import config
import helpers

BLOKKLISTE_JSON = os.path.join(SCRIPT_DIR, "blokkliste_store_utviklere.json")
RELEVANS_JSON = os.path.join(config.OUTPUT_DIR, "nyhetsbrev_relevans.json")
GRAYZONE_JSON = os.path.join(config.OUTPUT_DIR, "nyhetsbrev_grayzone.json")
CSV_OUT = os.path.join(config.OUTPUT_DIR, "followupboss-nyhetsbrev.csv")
HTML_OUT = os.path.join(config.OUTPUT_DIR, "nyhetsbrev-review.html")

# Kilder som regnes som "ekte" (verifiserte). guessed_pattern droppes alltid.
EKTE_KILDER = {"brreg", "hjemmeside_mailto", "hjemmeside_kontaktside", "hjemmeside_footer"}
KILDE_RANG = {"brreg": 0, "hjemmeside_mailto": 1, "hjemmeside_kontaktside": 2, "hjemmeside_footer": 3}

MAKS_EPOST_PER_SELSKAP = 3        # primær + 2 ekstra
GRAYZONE_OMSETNING = 30_000_000   # NOK
GRAYZONE_ANSATTE = 10

# FollowUpBoss-segmentering
TAGS = "Nybyggutvikler; Nyhetsbrev juni 2026"
SOURCE = "Eiendomsutvikler-scrape Oslo"

# Norske ordtegn for ordgrense-matching.
_ORD = "0-9a-zæøåäöüé"


# ---------------------------------------------------------------------------
# Små hjelpere (speiler 6_vasket_epost.py)
# ---------------------------------------------------------------------------
def _esc(v) -> str:
    return "" if v is None else html.escape(str(v))


def _norm(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", str(s).strip().lower())


def _ord_regex(frase: str) -> re.Pattern:
    kjerne = re.escape(_norm(frase))
    return re.compile(rf"(?<![{_ORD}]){kjerne}(?![{_ORD}])", re.IGNORECASE)


def _format_nok(v) -> str:
    if v is None or v == "":
        return ""
    try:
        n = int(v)
    except (ValueError, TypeError):
        return _esc(v)
    s = f"{abs(n):,}".replace(",", " ")
    return ("-" if n < 0 else "") + s


def _kilde_klasse(kilde: str) -> str:
    if kilde == "brreg":
        return "k-brreg"
    if kilde.startswith("hjemmeside"):
        return "k-trygg"
    return "k-other"


# ---------------------------------------------------------------------------
# Ekskludering av store utviklere — speiler 6_vasket_epost.py
# ---------------------------------------------------------------------------
def er_stor_utvikler(s: dict, store_regex: list[re.Pattern]) -> bool:
    navn = _norm(s.get("navn"))
    return any(rx.search(navn) for rx in store_regex)


# ---------------------------------------------------------------------------
# Aktør-nøkkel for dedup — speiler 6_vasket_epost.py
# ---------------------------------------------------------------------------
def aktor_key(s: dict) -> str:
    dl = _norm(s.get("daglig_leder"))
    if dl:
        return f"dl:{dl}"
    if s.get("spv_cluster_key"):
        return f"spv:{s['spv_cluster_key']}"
    sl = _norm(s.get("styreleder"))
    if sl:
        return f"sl:{sl}"
    return f"org:{s.get('orgnr')}"


# ---------------------------------------------------------------------------
# Gråsone-deteksjon
# ---------------------------------------------------------------------------
def er_grayzone(s: dict) -> bool:
    oms = s.get("omsetning_siste")
    ans = s.get("antall_ansatte")
    if isinstance(oms, (int, float)) and oms >= GRAYZONE_OMSETNING:
        return True
    if isinstance(ans, int) and ans >= GRAYZONE_ANSATTE:
        return True
    return False


# ---------------------------------------------------------------------------
# E-postvalg: person-e-post først, DL-proxy + presis navn-utledning
# ---------------------------------------------------------------------------
# Generiske local-parts som IKKE er personnavn (rolle/funksjon-innbokser).
_GENERISK_LOCAL = {
    "post", "kontakt", "kontakta", "info", "firmapost", "firmaepost", "mail", "mailbox",
    "hei", "hallo", "salg", "salgs", "marked", "marketing", "faktura", "invoice", "regnskap",
    "okonomi", "admin", "kontor", "resepsjon", "booking", "support", "kundeservice",
    "noreply", "varsling", "aapenhetsloven", "apenhetsloven", "eierskifte", "drift",
}


def _local_tokens(epost: str) -> list[str]:
    """Alfa-tokens i local-part, splittet på . _ - +."""
    local = epost.split("@")[0].lower()
    return [t for t in re.split(r"[._\-+]+", local) if t.isalpha() and len(t) >= 2]


def _er_generisk(epost: str) -> bool:
    toks = _local_tokens(epost)
    flat = re.sub(r"[^a-zæøå]", "", epost.split("@")[0].lower())
    return (not toks) or flat in _GENERISK_LOCAL or any(t in _GENERISK_LOCAL for t in toks)


def _person_tokens(navn: str) -> list[str]:
    return [t for t in _norm(navn).split() if len(t) >= 2]


def _personer(s: dict) -> list[str]:
    p = [x for x in [s.get("daglig_leder"), s.get("styreleder")] if x]
    p += [r.get("person_navn") for r in (s.get("andre_roller") or []) if r.get("person_navn")]
    return p


def _kjent_person(toks: list[str], personer: list[str]) -> str | None:
    """Match local-part mot kjent person via fornavn (første token, prefiks begge veier)."""
    if not toks:
        return None
    fn0 = toks[0]
    for navn in personer:
        pt = _person_tokens(navn)
        if pt and min(len(fn0), len(pt[0])) >= 3 and (fn0.startswith(pt[0]) or pt[0].startswith(fn0)):
            return navn
    return None


def velg_epost_nyhetsbrev(s: dict, domener_blokk: set[str]) -> list[dict]:
    """Velg opptil MAKS_EPOST_PER_SELSKAP ekte e-poster, person-først, DL-proxy øverst.
    Dropper e-poster på blokkerte domener (storaktør / konkurrerende meglere).
    Hvert valgt element får '_personlig' og '_is_dl'."""
    ekte = [dict(e) for e in s.get("emails", [])
            if e.get("kilde") in EKTE_KILDER and e.get("epost")
            and e["epost"].split("@")[-1].lower() not in domener_blokk]
    if not ekte:
        return []

    dl_fn = (_person_tokens(s.get("daglig_leder") or "") or [""])[0]
    for e in ekte:
        toks = _local_tokens(e["epost"])
        personlig = e.get("type") == "personal" and not _er_generisk(e["epost"])
        e["_personlig"] = personlig
        e["_is_dl"] = bool(personlig and dl_fn and toks
                           and min(len(toks[0]), len(dl_fn)) >= 3
                           and (toks[0].startswith(dl_fn) or dl_fn.startswith(toks[0])))

    def rank(e):
        if e["_is_dl"]:
            r = 0                       # DLs egen person-e-post
        elif e["_personlig"]:
            r = 1                       # annen navngitt person
        else:
            r = 2                       # rolle/generisk innboks (post@/kontakt@)
        return (r, KILDE_RANG.get(e.get("kilde"), 9), e["epost"].lower())

    ekte.sort(key=rank)

    valgt: list[dict] = []
    sett: set[str] = set()
    for e in ekte:
        adr = e["epost"].strip().lower()
        if adr in sett:
            continue
        # Rolle/generisk innboks kun som PRIMÆR (ingen person-e-post), aldri som ekstra.
        if not e["_personlig"] and valgt:
            continue
        sett.add(adr)
        valgt.append(e)
        if len(valgt) >= MAKS_EPOST_PER_SELSKAP:
            break
    return valgt


def kontaktnavn(e: dict, s: dict, er_primaer: bool) -> str:
    """Kontaktnavn — konservativt for å unngå feil hilsen i mail-merge:
      kjent person (via fornavn) > 'fornavn.etternavn' utledet > enkelt fornavn (>=4 tegn)
      > (kun rolle-innboks som primær) DL/styreleder > blankt."""
    if e.get("_personlig"):
        toks = _local_tokens(e["epost"])
        kjent = _kjent_person(toks, _personer(s))
        if kjent:
            return kjent
        if len(toks) >= 2:
            return f"{toks[0].title()} {toks[-1].title()}"
        if len(toks) == 1 and len(toks[0]) >= 4:   # enkelt fornavn; initialer (<4) → blankt
            return toks[0].title()
        return ""
    if er_primaer:                                 # rolle/generisk innboks → adresser DL
        return s.get("daglig_leder") or s.get("styreleder") or ""
    return ""


def split_navn(full: str) -> tuple[str, str]:
    full = (full or "").strip()
    if not full:
        return "", ""
    deler = full.split()
    if len(deler) == 1:
        return deler[0], ""
    return " ".join(deler[:-1]), deler[-1]


# ---------------------------------------------------------------------------
# Hovedpipeline
# ---------------------------------------------------------------------------
def main() -> int:
    master = helpers.load_json(config.MASTER_JSON, default=[])
    if not master:
        print(f"FEIL: tom eller manglende {config.MASTER_JSON}. Kjør 3_konsolider.py først.")
        return 1

    blokk = helpers.load_json(BLOKKLISTE_JSON, default={}) or {}
    # Merk: selger-blokken (Aubert/Daimyo/APT) er BFG8-spesifikk og brukes IKKE her —
    # den delte blokklista røres ikke (6_vasket_epost.py er avhengig av selger-delen).
    store_regex = [_ord_regex(x) for x in blokk.get("store_utviklere", []) if x]
    domener_blokk = {d.strip().lower() for d in blokk.get("domener", []) if d}

    relevans_doc = helpers.load_json(RELEVANS_JSON, default={}) or {}
    relevans = relevans_doc.get("verdikt", {}) if isinstance(relevans_doc, dict) else {}

    stats = {
        "stor_utvikler": 0, "ingen_epost": 0, "domene_blokk": 0,
        "auto_keep": 0, "gz_keep": 0, "gz_cut": 0, "gz_unknown": 0,
    }
    grayzone_dump: list[dict] = []   # alle gråsone-selskaper (til research)
    kandidater: list[dict] = []      # overlever filtrering (før aktør-dedup)

    for s in master:
        if er_stor_utvikler(s, store_regex):
            stats["stor_utvikler"] += 1
            continue
        valgt = velg_epost_nyhetsbrev(s, domener_blokk)
        if not valgt:
            ekte_all = [e for e in s.get("emails", [])
                        if e.get("kilde") in EKTE_KILDER and e.get("epost")]
            stats["domene_blokk" if ekte_all else "ingen_epost"] += 1
            continue

        gz = er_grayzone(s)
        verdikt = relevans.get(str(s.get("orgnr")))
        kilde_keep = "auto"   # auto | research-keep | research-unknown
        if gz:
            grayzone_dump.append({
                "orgnr": s.get("orgnr"), "navn": s.get("navn"),
                "omsetning_siste": s.get("omsetning_siste"),
                "antall_ansatte": s.get("antall_ansatte"),
                "hjemmeside": s.get("hjemmeside"),
                "daglig_leder": s.get("daglig_leder"),
                "naeringsbeskrivelse": s.get("naeringsbeskrivelse"),
            })
            if verdikt is None:
                stats["gz_unknown"] += 1
                kilde_keep = "research-unknown"   # behold, men flagg
            elif not verdikt.get("keep", True):
                stats["gz_cut"] += 1
                continue                          # research kuttet denne
            else:
                stats["gz_keep"] += 1
                kilde_keep = "research-keep"
        else:
            stats["auto_keep"] += 1

        kandidater.append({"selskap": s, "emails": valgt, "kilde_keep": kilde_keep,
                           "verdikt": verdikt})

    # Skriv alltid gråsone-dump (input til research-passet)
    helpers.save_json(GRAYZONE_JSON, {
        "_kommentar": "Gråsone-kandidater for nybygg-nyhetsbrevet (omsetning>=30M el. ansatte>=10). "
                      "Research hver og skriv verdikt til nyhetsbrev_relevans.json.",
        "terskel": {"omsetning": GRAYZONE_OMSETNING, "ansatte": GRAYZONE_ANSATTE},
        "antall": len(grayzone_dump),
        "selskaper": sorted(grayzone_dump, key=lambda d: -(d.get("omsetning_siste") or 0)),
    })

    # --- Aktør-dedup: én representant per aktør ---
    grupper: dict[str, list[dict]] = {}
    for k in kandidater:
        grupper.setdefault(aktor_key(k["selskap"]), []).append(k)

    def rep_score(k):
        s = k["selskap"]
        return (len(k["emails"]), s.get("omsetning_siste") or 0, -len(_norm(s.get("navn"))))

    n_sammenslatt = 0
    valgte = []
    for gruppe in grupper.values():
        gruppe.sort(key=rep_score, reverse=True)
        rep = gruppe[0]
        rep["merged"] = len(gruppe) - 1
        n_sammenslatt += len(gruppe) - 1
        valgte.append(rep)

    # --- Global dedup av eksakte adresser på tvers av selskaper ---
    valgte.sort(key=lambda k: _norm(k["selskap"].get("navn")))
    brukt: set[str] = set()
    endelige = []
    for k in valgte:
        beholdt = [e for e in k["emails"]
                   if e["epost"].strip().lower() not in brukt
                   and not brukt.add(e["epost"].strip().lower())]
        if not beholdt:
            continue
        k["emails"] = beholdt
        endelige.append(k)

    n_selskaper = len(endelige)
    n_rader = sum(len(k["emails"]) for k in endelige)

    _skriv_csv(endelige)
    _skriv_html(endelige, grayzone_dump, relevans, stats, n_selskaper, n_rader, n_sammenslatt)

    har_relevans = bool(relevans)
    print("FollowUpBoss-mottakerliste generert:")
    print(f"  Mottakere (selskaper):        {n_selskaper}")
    print(f"  Rader (e-postadresser):       {n_rader}")
    print(f"  Auto-keep (små, under terskel):{stats['auto_keep']}")
    print(f"  Gråsone keep (research):      {stats['gz_keep']}")
    print(f"  Gråsone cut (research):       {stats['gz_cut']}")
    print(f"  Gråsone UTEN verdikt (beholdt):{stats['gz_unknown']}")
    print(f"  Slått sammen (aktør/SPV/dup): {n_sammenslatt}")
    print(f"  Ekskludert – stor utvikler:   {stats['stor_utvikler']}")
    print(f"  Droppet – storaktør/megler-domene: {stats['domene_blokk']}")
    print(f"  Droppet – ingen ekte e-post:  {stats['ingen_epost']}")
    print()
    if not har_relevans:
        print(f"  ADVARSEL: {RELEVANS_JSON} mangler — hele gråsonen ({len(grayzone_dump)}) "
              f"er beholdt. Kjør research-passet og re-kjør.")
        print(f"  Gråsone-kandidater skrevet til: {GRAYZONE_JSON}")
    print(f"  CSV:  {CSV_OUT}")
    print(f"  open {HTML_OUT}")
    return 0


# ---------------------------------------------------------------------------
# CSV (FollowUpBoss)
# ---------------------------------------------------------------------------
FUB_HEADER = ["First Name", "Last Name", "Email", "Phone", "Company",
              "Tags", "Source", "Address", "City", "Zip", "Background"]


def _background(s: dict, e: dict) -> str:
    biter = [f"Orgnr {s.get('orgnr')}"]
    if s.get("hjemmeside"):
        biter.append(s["hjemmeside"])
    if s.get("omsetning_siste") is not None:
        biter.append(f"Omsetning {_format_nok(s.get('omsetning_siste'))}")
    biter.append(f"E-postkilde: {e.get('kilde', '')}")
    biter.append(f"Rolle: {e.get('type', '')}")
    return " · ".join(biter)


def _skriv_csv(endelige: list[dict]) -> None:
    with open(CSV_OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(FUB_HEADER)
        for k in endelige:
            s = k["selskap"]
            telefon = (s.get("telefoner") or [""])[0]
            for i, e in enumerate(k["emails"]):
                fornavn, etternavn = split_navn(kontaktnavn(e, s, er_primaer=(i == 0)))
                w.writerow([
                    fornavn, etternavn, e.get("epost", ""), telefon,
                    s.get("navn", ""), TAGS, SOURCE,
                    s.get("adresse", "") or "", s.get("poststed", "") or "",
                    s.get("postnr", "") or "", _background(s, e),
                ])


# ---------------------------------------------------------------------------
# HTML review
# ---------------------------------------------------------------------------
def _render_mottaker(k: dict) -> str:
    s = k["selskap"]
    navn, orgnr = s.get("navn", ""), s.get("orgnr", "")
    hjemmeside = s.get("hjemmeside") or ""
    merged = k.get("merged", 0)

    navn_html = (
        f'<div><b>{_esc(navn)}</b></div><div class="small">'
        f'<a href="https://w2.brreg.no/enhet/sok/detalj.jsp?orgnr={_esc(orgnr)}" target="_blank">{_esc(orgnr)}</a>'
    )
    if hjemmeside:
        navn_html += f' · <a href="{_esc(hjemmeside)}" target="_blank">hjemmeside ↗</a>'
    navn_html += "</div>"

    flagg = {"auto": '<span class="tag t-auto">auto</span>',
             "research-keep": '<span class="tag t-rk">research ✓</span>',
             "research-unknown": '<span class="tag t-unk">gråsone (uverifisert)</span>'}
    navn_html += " " + flagg.get(k.get("kilde_keep", "auto"), "")

    kontakt_html = ""
    for i, e in enumerate(k["emails"]):
        nm = kontaktnavn(e, s, er_primaer=(i == 0))
        rolle = "DL" if e.get("_is_dl") else ("primær" if i == 0 else "ekstra")
        kontakt_html += f'<div>{_esc(nm) or "<span class=small>(uten navn)</span>"} <span class="small">{rolle}</span></div>'
    if merged:
        kontakt_html += f'<div class="small merged">+{merged} aktør-søsken slått sammen</div>'

    chips = " ".join(
        f'<span class="email {_kilde_klasse(e.get("kilde",""))}" title="kilde: {_esc(e.get("kilde",""))} · {_esc(e.get("type",""))}">{_esc(e["epost"])}</span>'
        for e in k["emails"]
    )
    søk = " ".join(filter(None, [navn, orgnr, hjemmeside] + [e["epost"] for e in k["emails"]])).lower()
    return (
        f'<tr data-search="{_esc(søk)}">'
        f'<td>{navn_html}</td><td>{kontakt_html}</td><td>{chips}</td>'
        f'<td class="num">{_format_nok(s.get("omsetning_siste"))}</td></tr>'
    )


def _render_grayzone(grayzone_dump: list[dict], relevans: dict) -> str:
    rows = []
    for d in sorted(grayzone_dump, key=lambda x: -(x.get("omsetning_siste") or 0)):
        v = relevans.get(str(d.get("orgnr"))) or {}
        if not v:
            verd = '<span class="tag t-unk">uverifisert</span>'
        elif v.get("keep", True):
            verd = '<span class="tag t-rk">KEEP</span>'
        else:
            verd = '<span class="tag t-cut">CUT</span>'
        scale = _esc(v.get("scale", ""))
        inhouse = "ja" if v.get("in_house_sales") else ("nei" if v else "")
        rows.append(
            f'<tr><td><b>{_esc(d.get("navn"))}</b><div class="small">'
            f'<a href="https://w2.brreg.no/enhet/sok/detalj.jsp?orgnr={_esc(d.get("orgnr"))}" target="_blank">{_esc(d.get("orgnr"))}</a></div></td>'
            f'<td class="num">{_format_nok(d.get("omsetning_siste"))}</td>'
            f'<td>{verd}</td><td>{scale}</td><td>{_esc(inhouse)}</td>'
            f'<td class="small">{_esc(v.get("reason", ""))}</td>'
            f'<td class="small">{_esc(v.get("confidence", ""))}</td></tr>'
        )
    return "\n".join(rows)


_CSS = """
:root{--bg:#0f1419;--card:#1a2027;--border:#2d3848;--text:#e6edf3;--muted:#8b949e;
--accent:#58a6ff;--green:#3fb950;--red:#f85149;--amber:#e3b341}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:13px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{padding:16px 24px;background:var(--card);border-bottom:1px solid var(--border)}
h1{margin:0 0 8px;font-size:18px}h2{font-size:15px;margin:24px 24px 8px}
.meta{color:var(--muted);font-size:12px}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:10px 0}
.stat{background:var(--bg);border:1px solid var(--border);padding:6px 12px;border-radius:6px;font-size:12px}
.stat b{color:var(--accent);font-size:16px}.stat.warn b{color:var(--muted)}.stat.cut b{color:var(--red)}
.toolbar{margin:8px 0}
input[type=search]{width:100%;max-width:420px;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:6px 10px;border-radius:6px;font-size:13px}
.wrap{padding:0 24px 24px}
table{width:100%;border-collapse:separate;border-spacing:0;font-size:12px;margin-top:6px}
th{background:var(--card);text-align:left;padding:8px 6px;border-bottom:2px solid var(--border);white-space:nowrap}
td{padding:6px;border-bottom:1px solid var(--border);vertical-align:top}
tr:hover td{background:#161b22}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.email{display:inline-block;padding:1px 6px;border-radius:3px;margin:1px 2px 1px 0;font-size:11px;border:1px solid transparent}
.email.k-trygg{background:rgba(63,185,80,.15);color:#7ee787;border-color:rgba(63,185,80,.3)}
.email.k-brreg{background:rgba(88,166,255,.15);color:var(--accent);border-color:rgba(88,166,255,.3)}
.email.k-other{background:rgba(139,148,158,.15);color:var(--muted);border-color:rgba(139,148,158,.3)}
.small{color:var(--muted);font-size:11px}.merged{color:var(--amber)}
.tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:10px;font-weight:600}
.t-auto{background:rgba(139,148,158,.2);color:var(--muted)}
.t-rk{background:rgba(63,185,80,.2);color:#7ee787}
.t-cut{background:rgba(248,81,73,.2);color:#ff7b72}
.t-unk{background:rgba(210,153,34,.2);color:var(--amber)}
.hidden{display:none!important}
footer{padding:16px 24px 32px;color:var(--muted);font-size:11px;max-width:920px}
"""


def _skriv_html(endelige, grayzone_dump, relevans, stats, n_selskaper, n_rader, n_sammenslatt) -> None:
    mottakere_rows = "\n".join(_render_mottaker(k) for k in endelige)
    grayzone_rows = _render_grayzone(grayzone_dump, relevans)
    har_relevans = bool(relevans)
    gen = datetime.now().strftime("%Y-%m-%d %H:%M")

    advarsel = ""
    if not har_relevans:
        advarsel = ('<div class="stat cut" style="width:100%">⚠ nyhetsbrev_relevans.json mangler — '
                    f'hele gråsonen ({len(grayzone_dump)}) er beholdt uverifisert. Kjør research-passet.</div>')

    parts = [
        "<!DOCTYPE html><html lang=nb><head><meta charset=utf-8>",
        "<title>Nybygg-nyhetsbrev — mottakerliste (FollowUpBoss)</title>",
        f"<style>{_CSS}</style></head><body>",
        "<header><h1>Nybygg-nyhetsbrev — vasket mottakerliste</h1>",
        f'<div class="meta">Generert {gen} · kun ekte e-post · person-først (DL-proxy) · '
        "maks 3/selskap · aktør-dedup · store utviklere fjernet</div>",
        '<div class="stats">',
        f'<div class="stat">Mottakere: <b>{n_selskaper}</b></div>',
        f'<div class="stat">Rader: <b>{n_rader}</b></div>',
        f'<div class="stat">Auto-keep: <b>{stats["auto_keep"]}</b></div>',
        f'<div class="stat">Gråsone keep: <b>{stats["gz_keep"]}</b></div>',
        f'<div class="stat cut">Gråsone cut: <b>{stats["gz_cut"]}</b></div>',
        f'<div class="stat warn">Gråsone uverifisert: <b>{stats["gz_unknown"]}</b></div>',
        f'<div class="stat warn">Slått sammen: <b>{n_sammenslatt}</b></div>',
        f'<div class="stat warn">Ekskl. store utvikler: <b>{stats["stor_utvikler"]}</b></div>',
        f'<div class="stat warn">Droppet (storaktør/megler-domene): <b>{stats["domene_blokk"]}</b></div>',
        f'<div class="stat warn">Droppet (ingen e-post): <b>{stats["ingen_epost"]}</b></div>',
        advarsel,
        "</div></header>",
        f"<h2>Gråsone-verdikt ({len(grayzone_dump)})</h2>",
        '<div class="wrap"><table><thead><tr><th>Selskap</th><th class=num>Omsetning</th>'
        "<th>Verdikt</th><th>Skala</th><th>Eget meglerteam</th><th>Begrunnelse</th><th>Conf.</th></tr></thead>",
        f"<tbody>{grayzone_rows}</tbody></table></div>",
        "<h2>Mottakere</h2>",
        '<div class="toolbar wrap"><input type=search id=q placeholder="Søk selskap / e-post..."></div>',
        '<div class="wrap"><table id=tbl><thead><tr><th>Selskap</th><th>Kontakt(er)</th>'
        "<th>Valgte e-poster</th><th class=num>Omsetning</th></tr></thead>",
        f"<tbody>{mottakere_rows}</tbody></table></div>",
        "<footer>Vasket fra master.json for nybygg-nyhetsbrevet. Store utviklere fjernet via "
        "<code>blokkliste_store_utviklere.json</code>; gråsone (omsetning≥30M / ansatte≥10) verifisert "
        "via <code>nyhetsbrev_relevans.json</code> (hand-redigerbar). Person-e-post foretrekkes; "
        "rolle-innboks kun når ingen person-e-post finnes. Import-fil: <code>followupboss-nyhetsbrev.csv</code>.</footer>",
        "<script>",
        "const q=document.getElementById('q'),rows=[...document.querySelectorAll('#tbl tbody tr')];",
        "q.addEventListener('input',()=>{const s=q.value.toLowerCase().trim();",
        "for(const r of rows)r.classList.toggle('hidden',s&&!r.dataset.search.includes(s));});",
        "</script></body></html>",
    ]
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


if __name__ == "__main__":
    sys.exit(main())
