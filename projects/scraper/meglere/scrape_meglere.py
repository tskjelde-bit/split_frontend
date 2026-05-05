"""
Scrape ansattlister for alle Oslo-meglerkontor i meglere/alle_kontorer.md.

Bruker Camoufox med persistent_context (samme mønster som scripts_brev/).
Output: per kjede + aggregat JSON/CSV i meglere/output/.

Kjøring:
    python3 meglere/scrape_meglere.py                  # full scrape, resume
    python3 meglere/scrape_meglere.py --fresh          # start på nytt
    python3 meglere/scrape_meglere.py --kjede partners # bare én kjede
    python3 meglere/scrape_meglere.py --headed         # vis nettleser

Hver kjede:
  EM1, PrivatMegleren, DNB, Nordvik, Schala & Partners, Eie
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import time
from collections import defaultdict

from camoufox import Camoufox

# Sørg for at meglere/parsers er importerbar når scriptet kjøres direkte
HER = os.path.dirname(os.path.abspath(__file__))
PROSJEKT_ROT = os.path.dirname(HER)
if HER not in sys.path:
    sys.path.insert(0, HER)
if PROSJEKT_ROT not in sys.path:
    sys.path.insert(0, PROSJEKT_ROT)

from parsers import PARSERS, CLI_ALIAS, GENERELLE_DOMENE_PARSER  # noqa: E402
from urllib.parse import urlparse  # noqa: E402


# === KONFIG ===

KONTORLISTE_FIL = os.path.join(HER, "alle_kontorer.md")
OUTPUT_DIR = os.path.join(HER, "output")
PROGRESS_FIL = os.path.join(OUTPUT_DIR, "progress.json")
AGG_JSON = os.path.join(OUTPUT_DIR, "alle_meglere.json")
AGG_CSV = os.path.join(OUTPUT_DIR, "alle_meglere.csv")
BROWSER_PROFIL = os.path.join(PROSJEKT_ROT, ".browser_profil_meglere")

MIN_VENTETID = 8
MAX_VENTETID = 15
LANG_PAUSE_INTERVALL = 8
LANG_PAUSE = (25, 50)

KJEDE_FIL = {
    "EM1": "em1_ansatte.json",
    "PrivatMegleren": "privatmegleren_ansatte.json",
    "DNB": "dnb_ansatte.json",
    "Nordvik": "nordvik_ansatte.json",
    "Schala & Partners": "partners_ansatte.json",
    "Eie": "eie_ansatte.json",
    "Emera": "emera_ansatte.json",
    "Mekleriet": "mekleriet_ansatte.json",
    "Boa": "boa_ansatte.json",
    "Aktiv": "aktiv_ansatte.json",
    "Sem & Johnsen": "sem_johnsen_ansatte.json",
    "Generelle": "generelle_ansatte.json",
}

CSV_KOLONNER = [
    "kjede", "kontor", "fornavn", "etternavn", "fullt_navn",
    "rolle", "telefon", "telefon_normalisert", "epost",
    "kontor_url",
]


# === KONTORLISTE-PARSER ===

# Robust mot em-dash, en-dash, hyphen, kolon, og varierende mellomrom.
# Kolon krever space etter for å unngå at regexen kapser https:// fra URL-en.
_RE_KONTOR = re.compile(r"^(.+?)\s*(?:[–—-]\s*|:\s+)(https?://\S+)\s*$")
_KJEDE_HEADER_MAP = {
    "em1": "EM1",
    "privatmegleren": "PrivatMegleren",
    "dnb": "DNB",
    "nordvik": "Nordvik",
    "schala & partners": "Schala & Partners",
    "schala": "Schala & Partners",
    "eie": "Eie",
    "emera": "Emera",
    "mekleriet": "Mekleriet",
    "boa": "Boa",
    "aktiv": "Aktiv",
    "sem & johnsen": "Sem & Johnsen",
    "sem og johnsen": "Sem & Johnsen",
    "generelle": "Generelle",
}

# Navn-prefiks per kjede der enkeltlinje noen ganger inneholder flere navn+URL
# konkatenert (f.eks. "Aktiv Xhttps://...Aktiv Yhttps://..."). Brukes til
# å splitte slike linjer.
_KJEDE_NAVN_PREFIKS = {
    "Aktiv": "Aktiv",
}


def _splitt_konkatenert(linje, prefiks):
    """Splitter 'PrefiksNavn1URL1PrefiksNavn2URL2...' til [(navn, url), ...]."""
    pattern = re.compile(
        rf"({re.escape(prefiks)}\s.*?)(https?://\S+?)(?={re.escape(prefiks)}\s|$)"
    )
    matches = pattern.findall(linje)
    return [(navn.strip(), url) for navn, url in matches]


def les_kontorliste(md_path):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Fant ikke kontorliste: {md_path}")

    kontorer = []
    aktiv_kjede = None

    with open(md_path, encoding="utf-8") as f:
        for raa in f:
            linje = raa.strip()
            if not linje:
                continue

            # Header-deteksjon: aksepter både med og uten avsluttende kolon
            kandidat_header = linje.rstrip(":").strip().lower()
            if kandidat_header in _KJEDE_HEADER_MAP:
                aktiv_kjede = _KJEDE_HEADER_MAP[kandidat_header]
                continue

            if aktiv_kjede is None:
                continue

            # Hvis linjen har flere URL-er konkatenert (Aktiv-mønsteret),
            # splitte til (navn, url)-par først.
            if linje.count("http") > 1:
                prefiks = _KJEDE_NAVN_PREFIKS.get(aktiv_kjede)
                if prefiks:
                    par = _splitt_konkatenert(linje, prefiks)
                    for navn, url in par:
                        kontorer.append({
                            "kjede": aktiv_kjede,
                            "kontor": navn,
                            "url": url.rstrip(",.;)"),
                        })
                    continue

            m = _RE_KONTOR.match(linje)
            if not m:
                continue

            kontor_navn = m.group(1).strip()
            url = m.group(2).rstrip(",.;)")
            kontorer.append({
                "kjede": aktiv_kjede,
                "kontor": kontor_navn,
                "url": url,
            })

    return kontorer


# === IO-HJELPERE ===

def lagre_json_atomisk(data, sti):
    os.makedirs(os.path.dirname(sti), exist_ok=True)
    tmp = sti + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, sti)


def lagre_csv_atomisk(data, sti):
    os.makedirs(os.path.dirname(sti), exist_ok=True)
    tmp = sti + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_KOLONNER, extrasaction="ignore")
        writer.writeheader()
        for rad in data:
            writer.writerow(rad)
    os.replace(tmp, sti)


def les_json_om_finnes(sti, default):
    if not os.path.exists(sti):
        return default
    try:
        with open(sti, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def lagre_debug_html(html, kjede, kontor_url):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", kontor_url.lower()).strip("_")[:80]
    sti = os.path.join(OUTPUT_DIR, f"debug_{kjede.lower().replace(' ', '_')}_{slug}.html")
    with open(sti, "w", encoding="utf-8") as f:
        f.write(html)
    return sti


# === ANTI-BOT-PAUSE ===

_request_teller = 0


def smart_pause(label=""):
    global _request_teller
    _request_teller += 1
    if _request_teller % LANG_PAUSE_INTERVALL == 0:
        pause = random.uniform(*LANG_PAUSE)
        print(f"    (Lang pause: {pause:.0f} s)")
    else:
        pause = random.uniform(MIN_VENTETID, MAX_VENTETID)
    time.sleep(pause)


# === SIDE-HENTING ===

def hent_side(page, url, parser_modul=None):
    # domcontentloaded > networkidle: noen sider (Emera) har vedvarende
    # analytics-trafikk som aldri går idle. Parsers som trenger JS-rendret
    # innhold venter selv via pre_load (wait_for_selector + scroll).
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception:
        # Fallback: prøv en gang til med kortere timeout
        page.goto(url, wait_until="commit", timeout=15000)
    time.sleep(random.uniform(1.0, 2.0))
    if parser_modul is not None and hasattr(parser_modul, "pre_load"):
        try:
            parser_modul.pre_load(page, url)
        except Exception as e:
            print(f"    (pre_load-feil ignoreres: {e})")
    return page.content()


# === HOVEDPROGRAM ===

def parse_args():
    ap = argparse.ArgumentParser(description="Scrape ansattlister fra Oslo-meglerkontor")
    ap.add_argument("--fresh", action="store_true", help="Slett progress + output, start på nytt")
    ap.add_argument("--kjede", help="Bare én kjede (em1|privatmegleren|dnb|nordvik|partners|eie)")
    ap.add_argument("--headed", action="store_true", help="Vis nettleser-vinduet (default: headless)")
    return ap.parse_args()


def main():
    args = parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    kjede_filter = None
    if args.kjede:
        nokkel = args.kjede.lower().strip()
        if nokkel not in CLI_ALIAS:
            print(f"FEIL: ukjent kjede '{args.kjede}'. Gyldige: {', '.join(CLI_ALIAS)}")
            sys.exit(1)
        kjede_filter = CLI_ALIAS[nokkel]

    if args.fresh:
        print("FRESH-modus: sletter output + progress")
        for navn in os.listdir(OUTPUT_DIR) if os.path.exists(OUTPUT_DIR) else []:
            sti = os.path.join(OUTPUT_DIR, navn)
            if os.path.isfile(sti):
                os.remove(sti)

    kontorer = les_kontorliste(KONTORLISTE_FIL)
    if kjede_filter:
        kontorer = [k for k in kontorer if k["kjede"] == kjede_filter]
    if not kontorer:
        print("Ingen kontor å scrape. Avslutter.")
        return

    progress = les_json_om_finnes(PROGRESS_FIL, {})
    per_kjede = defaultdict(list)
    for kjede, filnavn in KJEDE_FIL.items():
        per_kjede[kjede] = les_json_om_finnes(os.path.join(OUTPUT_DIR, filnavn), [])

    print(f"\nKlar til å scrape {len(kontorer)} kontor.")
    if kjede_filter:
        print(f"Filter: bare {kjede_filter}")
    if progress:
        ferdige = sum(1 for v in progress.values() if v.get("ferdig"))
        print(f"Resume: {ferdige} kontor er allerede ferdige")

    os.makedirs(BROWSER_PROFIL, exist_ok=True)
    print(f"Starter Camoufox (profil: {BROWSER_PROFIL})...")

    with Camoufox(
        persistent_context=True,
        headless=not args.headed,
        humanize=True,
        geoip=True,
        locale="nb-NO",
        enable_cache=True,
        user_data_dir=BROWSER_PROFIL,
    ) as context:
        page = context.new_page()

        for idx, kontor in enumerate(kontorer, start=1):
            kjede = kontor["kjede"]
            url = kontor["url"]
            navn = kontor["kontor"]
            etikett = f"[{idx}/{len(kontorer)}] {kjede} — {navn}"

            if progress.get(url, {}).get("ferdig"):
                print(f"{etikett}: FERDIG (resume) — hopper over")
                continue

            # Generelle: dispatch til riktig parser basert på URL-domene
            if kjede == "Generelle":
                host = urlparse(url).netloc.lower()
                if host.startswith("www."):
                    host = host[4:]
                parser_modul = GENERELLE_DOMENE_PARSER.get(host)
                if parser_modul is None:
                    print(f"{etikett}: SKIPPET — ingen Generelle-parser for domene '{host}'")
                    continue
            else:
                parser_modul = PARSERS.get(kjede)
                if parser_modul is None:
                    print(f"{etikett}: SKIPPET — ingen parser for kjede '{kjede}'")
                    continue

            print(f"{etikett}")
            print(f"    -> {url}")

            try:
                html = hent_side(page, url, parser_modul)
            except Exception as e:
                print(f"    FEIL ved henting: {e}")
                progress[url] = {"ferdig": False, "feil": str(e)[:200]}
                lagre_json_atomisk(progress, PROGRESS_FIL)
                smart_pause()
                continue

            try:
                ansatte = parser_modul.parse(html, page, navn, url)
                # Generelle-records skal tagges med "Generelle", ikke domenets kjede
                if kjede == "Generelle":
                    for r in ansatte:
                        r["kjede"] = "Generelle"
            except Exception as e:
                print(f"    FEIL ved parsing: {e}")
                debug_sti = lagre_debug_html(html, kjede, url)
                print(f"    Debug-HTML lagret: {debug_sti}")
                progress[url] = {"ferdig": False, "feil": f"parse: {e}"[:200]}
                lagre_json_atomisk(progress, PROGRESS_FIL)
                smart_pause()
                continue

            if not ansatte:
                debug_sti = lagre_debug_html(html, kjede, url)
                print(f"    0 ansatte funnet — debug-HTML: {debug_sti}")
                progress[url] = {"ferdig": True, "antall": 0, "advarsel": "tom liste"}
            else:
                # Erstatt eventuelle tidligere oppføringer for dette kontoret
                per_kjede[kjede] = [a for a in per_kjede[kjede] if a.get("kontor_url") != url]
                per_kjede[kjede].extend(ansatte)
                progress[url] = {"ferdig": True, "antall": len(ansatte)}
                print(f"    {len(ansatte)} ansatte")

            # Skriv per-kjede + aggregat etter hver runde
            lagre_json_atomisk(per_kjede[kjede], os.path.join(OUTPUT_DIR, KJEDE_FIL[kjede]))
            alle = [r for liste in per_kjede.values() for r in liste]
            lagre_json_atomisk(alle, AGG_JSON)
            lagre_csv_atomisk(alle, AGG_CSV)
            lagre_json_atomisk(progress, PROGRESS_FIL)

            smart_pause(etikett)

        page.close()

    # Sluttsammendrag
    print("\n" + "=" * 60)
    print("FERDIG.")
    totalt = 0
    for kjede in KJEDE_FIL:
        antall = len(per_kjede.get(kjede, []))
        totalt += antall
        print(f"  {kjede:20s} {antall:>5} ansatte")
    print(f"  {'TOTALT':20s} {totalt:>5}")
    print(f"\n  JSON:  {AGG_JSON}")
    print(f"  CSV:   {AGG_CSV}")
    tomme = [u for u, v in progress.items() if v.get("antall") == 0 or v.get("advarsel")]
    if tomme:
        print(f"\n  ADVARSEL: {len(tomme)} kontor ga 0 ansatte — sjekk debug-HTML i {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
