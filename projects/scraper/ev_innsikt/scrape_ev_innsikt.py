"""
Scraper for EV Innsikt (Power BI) — henter bydel-statistikk for Oslo.

Henter data fra 3 Power BI-sider via Export data → Summarized data → .xlsx:
  - Prisutvikling (kvartalsvis prisendring per bydel)
  - Omsetningstid (salgstid i dager per bydel)
  - Snittpris (totalpriser + m²-priser per bydel, to tabs på samme side)

Bruker cookies fra Dia-nettleseren (headless). Krever at du er logget inn
på Power BI i Dia før scriptet kjøres.

BRUK:
  python3 scrape_ev_innsikt.py                      # Full scrape
  python3 scrape_ev_innsikt.py --debug               # Lagre screenshots
  python3 scrape_ev_innsikt.py --page prisutvikling  # Kun én side
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from pycookiecheat import chrome_cookies
import json
import time
import os
import sys
import signal
import subprocess
import argparse
import re
from datetime import datetime


# === KONFIGURASJON ===

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = SCRIPT_DIR
OUTPUT_JSON = os.path.join(OUTPUT_DIR, 'bydel_statistikk.json')
DOWNLOAD_DIR = os.path.join(OUTPUT_DIR, 'downloads')
BROWSER_PROFIL = os.path.join(OUTPUT_DIR, '.browser_profil')
DEBUG_DIR = os.path.join(OUTPUT_DIR, 'debug')

APP_ID = '8b0bdea8-9fab-4c4f-b70a-8c4563a780fa'
REPORT_ID = 'bd55a995-d91c-4d05-b53c-e4754e612277'
TENANT_ID = 'e3f99559-2ef3-482b-8ad9-dd9a2cfef44c'
PBI_BASE = 'https://app.powerbi.com'

SIDER = {
    'prisutvikling': {
        'reportPage': 'ReportSectionb65f7c9407da34109524',
        'felt': 'priceChange',
    },
    'omsetningstid': {
        'reportPage': 'ReportSectionff94e153e223ac9050bd',
        'felt': 'avgDaysOnMarket',
    },
    'snittpris': {
        'reportPage': 'ReportSectiona11558d7b88d306016b2',
        'felt': 'medianPrice',
    },
    'snittpris_m2': {
        'reportPage': 'ReportSectiona11558d7b88d306016b2',
        'felt': 'pricePerSqm',
    },
    # Tidsserie-sider: hver eksport returnerer per-bydel serie (dato/måned + verdi)
    'antall_solgt': {
        'reportPage': 'ReportSection3a5d1600620c9b72e1ce',
        'bookmark':   'dce5b96a-ba5d-4298-bb7e-63bda221f7a8',
        'visual':     '5b800857d0b54c3cb7d8',
        'felt':       'salesPerMonth',
        'timeseries': 'monthly',
    },
    'antall_til_salgs': {
        'reportPage': 'ReportSection417df07e636de500d7d9',
        'bookmark':   '7689b98a-9557-4c31-9b0e-7a32bc4c0391',
        'visual':     '5b800857d0b54c3cb7d8',
        'felt':       'listingsPerMonth',
        'timeseries': 'monthly',
    },
    'prisindeks': {
        'reportPage': 'ReportSectionb65f7c9407da34109524',
        'bookmark':   '95be46a9-85a6-4e6d-a45d-2d42c6a0c872',
        'visual':     'da683d59f7b0a8c36014',
        'felt':       'priceIndex',
        'timeseries': 'daily',
    },
}

VENTETID_MELLOM_SIDER = 5
VENT_ETTER_NAVIGERING = 12
VENT_ETTER_FILTER = 3

OSLO_BYDELER = {
    'gamle-oslo':        'Gamle Oslo',
    'grunerlokka':       'Grünerløkka',
    'sagene':            'Sagene',
    'st-hanshaugen':     'St. Hanshaugen',
    'sentrum':           'Sentrum',
    'frogner':           'Frogner',
    'ullern':            'Ullern',
    'vestre-aker':       'Vestre Aker',
    'nordre-aker':       'Nordre Aker',
    'bjerke':            'Bjerke',
    'grorud':            'Grorud',
    'stovner':           'Stovner',
    'alna':              'Alna',
    'ostensjo':          'Østensjø',
    'nordstrand':        'Nordstrand',
    'sondre-nordstrand': 'Søndre Nordstrand',
}

BYDEL_NORMALISERING = {}

def _bygg_normalisering():
    varianter = {
        'gamle-oslo':        ['gamle oslo', 'gamleoslo', 'oslo: gamle oslo'],
        'grunerlokka':       ['grünerløkka', 'grunerløkka', 'grunerlokka', 'oslo: grünerløkka',
                              'oslo: grünerlø…', 'oslo: grünerlo…'],
        'sagene':            ['sagene', 'oslo: sagene'],
        'st-hanshaugen':     ['st. hanshaugen', 'st.hanshaugen', 'st hanshaugen',
                              'st.hans…', 'oslo: st.hanshaugen', 'oslo: st. hanshaugen'],
        'sentrum':           ['sentrum', 'oslo: sentrum'],
        'frogner':           ['frogner', 'oslo: frogner'],
        'ullern':            ['ullern', 'oslo: ullern'],
        'vestre-aker':       ['vestre aker', 'oslo: vestre aker'],
        'nordre-aker':       ['nordre aker', 'oslo: nordre aker'],
        'bjerke':            ['bjerke', 'oslo: bjerke'],
        'grorud':            ['grorud', 'oslo: grorud'],
        'stovner':           ['stovner', 'oslo: stovner'],
        'alna':              ['alna', 'oslo: alna'],
        'ostensjo':          ['østensjø', 'ostensjø', 'ostensjo', 'oslo: østensjø'],
        'nordstrand':        ['nordstrand', 'oslo: nordstrand'],
        'sondre-nordstrand': ['søndre nordstrand', 'sondre nordstrand',
                              'oslo: søndre nordstrand', 'søndre nordstra…'],
    }
    for bydel_id, navnliste in varianter.items():
        for navn in navnliste:
            BYDEL_NORMALISERING[navn.lower().strip()] = bydel_id
        BYDEL_NORMALISERING[bydel_id] = bydel_id

_bygg_normalisering()


def normaliser_bydel(navn):
    if not navn:
        return None
    rent = navn.lower().strip()
    rent = re.sub(r'^oslo:\s*', '', rent)
    if rent in BYDEL_NORMALISERING:
        return BYDEL_NORMALISERING[rent]
    if len(rent) >= 5:
        for noekkel, bydel_id in BYDEL_NORMALISERING.items():
            if len(noekkel) >= 5 and rent.startswith(noekkel):
                return bydel_id
    return None


OSLO_FYLKE_NAVN = {'oslo', 'oslo fylke', 'oslo kommune'}

_stopp = False
def _sigint_handler(sig, frame):
    global _stopp
    if not _stopp:
        _stopp = True
        print("\n  Avslutning forespurt — stopper etter nåværende operasjon...")
    else:
        sys.exit(130)
signal.signal(signal.SIGINT, _sigint_handler)


# === POWER BI URL ===

def pbi_url(report_page, bookmark_guid=None, visual=None):
    """Bygger URL til Power BI-rapport.

    Hvis `visual` er satt bygger vi en shareVisual-URL som åpner visualen i
    fokus-modus (full-screen) — dette omgår problemet med å finne riktig
    visual i en side med mange elementer.
    """
    source = 'shareVisual' if visual else 'appShareLink'
    url = (
        f'{PBI_BASE}/Redirect?action=OpenReport'
        f'&appId={APP_ID}'
        f'&reportObjectId={REPORT_ID}'
        f'&ctid={TENANT_ID}'
        f'&reportPage={report_page}'
        f'&pbi_source={source}'
    )
    if visual:
        url += f'&visual={visual}'
    if bookmark_guid:
        url += f'&bookmarkGuid={bookmark_guid}'
    return url


# === XLSX PARSING ===

def parse_xlsx(filsti):
    """Parser eksportert .xlsx fra Power BI. Returnerer dict[bydel_id] -> verdi."""
    try:
        import openpyxl
    except ImportError:
        print('    FEIL: openpyxl ikke installert — kjør: pip install openpyxl')
        return {}, None

    wb = openpyxl.load_workbook(filsti, data_only=True)
    ws = wb.active

    if ws.max_row < 2:
        print(f'    Tom xlsx: {filsti}')
        return {}, None

    header = [str(cell.value or '').strip() for cell in ws[1]]
    print(f'    Kolonner: {header}')

    # Finn bydel-kolonne og verdi-kolonne
    bydel_col = 0
    verdi_col = 1

    for i, h in enumerate(header):
        hl = h.lower()
        if any(k in hl for k in ['område', 'bydel', 'district', 'region', 'kommune']):
            bydel_col = i
        elif any(k in hl for k in ['gjennomsnitt', 'snitt', 'median', 'pris', 'verdi',
                                     'value', 'dager', 'days', 'endring', 'change',
                                     'omsetningstid', 'm²', 'm2', 'kvm']):
            verdi_col = i

    resultat = {}
    oslo_total = None

    for row in ws.iter_rows(min_row=2, values_only=True):
        if len(row) <= max(bydel_col, verdi_col):
            continue
        navn = row[bydel_col]
        verdi = row[verdi_col]
        if not navn or verdi is None:
            continue

        navn_str = str(navn).strip()
        try:
            verdi_num = float(verdi)
        except (ValueError, TypeError):
            # Prøv å fjerne mellomrom og prosenttegn
            try:
                verdi_num = float(str(verdi).replace(' ', '').replace('%', '').replace(',', '.'))
            except (ValueError, TypeError):
                continue

        bydel_id = normaliser_bydel(navn_str)
        if bydel_id:
            resultat[bydel_id] = verdi_num
        elif navn_str.lower().strip() in OSLO_FYLKE_NAVN:
            oslo_total = verdi_num

    print(f'    Parsert: {len(resultat)} bydeler')
    return resultat, oslo_total


MAANEDER_NB = {
    'januar': 1, 'februar': 2, 'mars': 3, 'april': 4, 'mai': 5, 'juni': 6,
    'juli': 7, 'august': 8, 'september': 9, 'oktober': 10, 'november': 11, 'desember': 12,
}
MAANED_NAVN = {v: k for k, v in MAANEDER_NB.items()}


def _parse_dato(verdi):
    """Returnerer (year, month_number, iso_date or None) eller None."""
    if verdi is None:
        return None
    if isinstance(verdi, datetime):
        return verdi.year, verdi.month, verdi.date().isoformat()
    s = str(verdi).strip().lower()
    if not s:
        return None
    # "januar 2026", "jan 2026", "januar"
    for navn, nr in MAANEDER_NB.items():
        if s.startswith(navn) or s.startswith(navn[:3]):
            m = re.search(r'(19|20)\d{2}', s)
            year = int(m.group(0)) if m else None
            return year, nr, None
    # "2026-01-15", "15.01.2026", "15/01/2026"
    m = re.match(r'^(\d{4})-(\d{1,2})(?:-(\d{1,2}))?', s)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3) or '01'
        return int(y), int(mo), f'{int(y):04d}-{int(mo):02d}-{int(d):02d}'
    m = re.match(r'^(\d{1,2})[./-](\d{1,2})[./-](\d{4})', s)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        return int(y), int(mo), f'{int(y):04d}-{int(mo):02d}-{int(d):02d}'
    # Kun årstall
    m = re.match(r'^(19|20)\d{2}$', s)
    if m:
        return int(s), None, None
    return None


_BYDEL_KEYS = ('område', 'bydel', 'district', 'region', 'kommune')


def _finn_header_rad(rader):
    """Scanner et iterable av rader og returnerer (header_index, header_cols).

    PBI-eksporter har 2-3 metadatarader ("Brukte filtre:...") før den faktiske
    kolonne-headeren. Vi identifiserer headeren ved at én celle ER et
    bydel-keyword (Område / Bydel / District / ...).

    Vi krever at cellen er kort (≤40 tegn) og uten linjeskift, slik at vi
    ikke matcher metadata-blober som "CityDistrictName er OSLO\\n...".
    """
    rader = list(rader)
    for idx, row in enumerate(rader):
        cols = [str(c).strip() if c is not None else '' for c in row]
        for c in cols:
            if len(c) > 40 or '\n' in c:
                continue
            cl = c.lower()
            if any(cl == k or cl.startswith(k) for k in _BYDEL_KEYS):
                return idx, cols, rader
    if rader:
        return 0, [str(c).strip() if c is not None else '' for c in rader[0]], rader
    return 0, [], []


def _identifiser_timeseries_kolonner(header):
    bydel_col = dato_col = verdi_col = aar_col = maaned_col = None
    for i, h in enumerate(header):
        hl = h.lower()
        if bydel_col is None and any(k in hl for k in _BYDEL_KEYS):
            bydel_col = i
        elif any(k in hl for k in ['dato', 'date']):
            dato_col = i
        elif hl in ('år', 'aar', 'year'):
            aar_col = i
        elif hl in ('måned', 'maaned', 'month', 'monthname'):
            maaned_col = i
        elif verdi_col is None and any(k in hl for k in [
            'antall', 'solgt', 'lagtut', 'lagt ut', 'til salgs', 'indeks',
            'prisendring', 'verdi', 'value', 'pris', 'count', 'totalt',
        ]):
            verdi_col = i

    if verdi_col is None:
        for i in range(len(header)):
            if i in (bydel_col, dato_col, aar_col, maaned_col):
                continue
            verdi_col = i
            break

    return bydel_col, dato_col, verdi_col, aar_col, maaned_col


def _parse_timeseries_rows(rader, header_idx, header, kind):
    """Tar rå rader + header-info og returnerer (per_bydel, oslo_series)."""
    bydel_col, dato_col, verdi_col, aar_col, maaned_col = _identifiser_timeseries_kolonner(header)
    if bydel_col is None or verdi_col is None:
        print(f'    FEIL: Fant ikke bydel/verdi-kolonne i {header}')
        return {}, []

    per_bydel = {}
    oslo_series = []

    for row in rader[header_idx + 1:]:
        if len(row) <= max(c for c in [bydel_col, verdi_col, dato_col, aar_col, maaned_col] if c is not None):
            continue
        navn = row[bydel_col]
        verdi = row[verdi_col]
        if navn is None or verdi is None:
            continue

        try:
            verdi_num = float(verdi)
        except (ValueError, TypeError):
            try:
                verdi_num = float(str(verdi).replace(' ', '').replace('%', '').replace(',', '.'))
            except (ValueError, TypeError):
                continue

        # Tidsinfo
        year = month = iso = None
        if dato_col is not None:
            parsed = _parse_dato(row[dato_col])
            if parsed:
                year, month, iso = parsed
        if year is None and aar_col is not None:
            try:
                year = int(row[aar_col])
            except (TypeError, ValueError):
                pass
        if month is None and maaned_col is not None:
            parsed = _parse_dato(row[maaned_col])
            if parsed:
                _, month, _ = parsed

        navn_str = str(navn).strip()
        bydel_id = normaliser_bydel(navn_str)
        er_oslo = navn_str.lower().strip() in OSLO_FYLKE_NAVN

        if kind == 'monthly':
            if month is None or year is None:
                continue
            entry = {'year': year, 'month': MAANED_NAVN[month], 'count': int(round(verdi_num))}
        else:  # daily
            if iso is None:
                if year is not None and month is not None:
                    iso = f'{year:04d}-{month:02d}-01'
                else:
                    continue
            entry = {'date': iso, 'value': round(verdi_num, 3)}

        if bydel_id:
            per_bydel.setdefault(bydel_id, []).append(entry)
        elif er_oslo:
            oslo_series.append(entry)

    def _sort_key(e):
        if 'date' in e:
            return e['date']
        return (e['year'], MAANEDER_NB.get(e['month'], 0))

    for arr in per_bydel.values():
        arr.sort(key=_sort_key)
    oslo_series.sort(key=_sort_key)

    return per_bydel, oslo_series


def parse_xlsx_timeseries(filsti, kind='monthly'):
    """Parser timeseries-xlsx fra Power BI.

    Returnerer (dict[bydel_id] -> [entry, ...], oslo_series).
    Entry for 'monthly' = {year, month, count} (month = norsk navn).
    Entry for 'daily'   = {date, value}.
    """
    try:
        import openpyxl
    except ImportError:
        print('    FEIL: openpyxl ikke installert — kjør: pip install openpyxl')
        return {}, []

    wb = openpyxl.load_workbook(filsti, data_only=True)
    ws = wb.active
    if ws.max_row < 2:
        print(f'    Tom xlsx: {filsti}')
        return {}, []

    rader_raw = [tuple(r) for r in ws.iter_rows(values_only=True)]
    header_idx, header, rader = _finn_header_rad(rader_raw)
    print(f'    Kolonner (rad {header_idx + 1}): {header}')

    per_bydel, oslo_series = _parse_timeseries_rows(rader, header_idx, header, kind)
    print(f'    Parsert tidsserie: {len(per_bydel)} bydeler, {sum(len(v) for v in per_bydel.values())} datapunkter' +
          (f', {len(oslo_series)} Oslo-punkter' if oslo_series else ''))
    return per_bydel, oslo_series


def parse_csv_timeseries(filsti, kind='monthly'):
    """Parser timeseries-CSV fra Power BI (Oppsummerte data → CSV-format).

    CSV-eksporter fra PBI-linjediagram har form:
      rad 1: "Brukte filtre: ..." (kan ha komma — quotes håndterer det)
      rad 2: (blank)
      rad 3+: faktisk header + data, f.eks. "Dato,Område,Indeks".
    """
    import csv

    try:
        with open(filsti, 'r', encoding='utf-8-sig', newline='') as f:
            rader_raw = [tuple(row) for row in csv.reader(f)]
    except UnicodeDecodeError:
        with open(filsti, 'r', encoding='latin-1', newline='') as f:
            rader_raw = [tuple(row) for row in csv.reader(f)]

    if not rader_raw:
        print(f'    Tom csv: {filsti}')
        return {}, []

    header_idx, header, rader = _finn_header_rad(rader_raw)
    print(f'    Kolonner (rad {header_idx + 1}): {header}')

    per_bydel, oslo_series = _parse_timeseries_rows(rader, header_idx, header, kind)
    print(f'    Parsert tidsserie: {len(per_bydel)} bydeler, {sum(len(v) for v in per_bydel.values())} datapunkter' +
          (f', {len(oslo_series)} Oslo-punkter' if oslo_series else ''))
    return per_bydel, oslo_series


# === BROWSER ===

DIA_COOKIE_FILE = os.path.expanduser(
    '~/Library/Application Support/Dia/User Data/Default/Cookies'
)

PBI_COOKIE_DOMAINS = [
    'https://app.powerbi.com',
    'https://login.microsoftonline.com',
    'https://login.live.com',
    'https://aadcdn.msftauth.net',
    'https://wabi-north-europe-j-primary-redirect.analysis.windows.net',
]


def _hent_dia_passord():
    """Hent dekrypteringsnøkkel for Dia-cookies fra macOS Keychain."""
    try:
        return subprocess.check_output(
            ['security', 'find-generic-password', '-s', 'Dia Safe Storage', '-w'],
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def hent_pbi_cookies():
    if not os.path.exists(DIA_COOKIE_FILE):
        print('  FEIL: Dia cookie-database ikke funnet.')
        print(f'  Forventet: {DIA_COOKIE_FILE}')
        return []

    dia_pwd = _hent_dia_passord()
    if not dia_pwd:
        print('  FEIL: Kunne ikke hente "Dia Safe Storage" fra Keychain.')
        return []

    pw_cookies = []
    for url in PBI_COOKIE_DOMAINS:
        try:
            cookies = chrome_cookies(url, cookie_file=DIA_COOKIE_FILE, password=dia_pwd)
        except Exception as e:
            print(f'  Advarsel: Kunne ikke hente cookies for {url}: {e}')
            continue
        domain = url.replace('https://', '')
        for name, value in (cookies or {}).items():
            pw_cookies.append({
                'name': name,
                'value': value,
                'domain': domain,
                'path': '/',
            })
    print(f'  {len(pw_cookies)} cookies hentet fra Dia')
    return pw_cookies


def lag_browser_og_context(pw):
    cookies = hent_pbi_cookies()
    if not cookies:
        print('  FEIL: Ingen cookies funnet. Logg inn på Power BI i Dia først.')
        sys.exit(1)

    browser = pw.chromium.launch(
        headless=True,
    )
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        locale='nb-NO',
        accept_downloads=True,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    )
    context.add_cookies(cookies)
    return browser, context


def er_pbi_innlogget(page):
    url = page.url
    if any(k in url for k in ['login.microsoftonline', 'login.live', 'oauth']):
        return False
    # Power BI kan vise innloggingsskjema uten URL-redirect
    try:
        if page.locator('input[placeholder="Enter email"]').is_visible(timeout=2000):
            return False
        if page.locator('text="Skriv inn e-postadressen din"').is_visible(timeout=1000):
            return False
    except Exception:
        pass
    return True


# === EKSPORT FRA POWER BI ===

def finn_pbi_frame(page, debug=False):
    """Finn Power BI rapport-framen. Returnerer frame eller page hvis ingen iframe."""
    for frame in page.frames:
        url = frame.url
        if any(k in url for k in ['reportEmbed', 'reportLanding', '/reports/', 'rdlEmbed']):
            if debug:
                print(f'    [debug] Bruker iframe: {url[:80]}')
            return frame
    if debug:
        print(f'    [debug] Ingen rapport-iframe funnet, bruker hovedframe')
        for i, f in enumerate(page.frames):
            print(f'    [debug]   frame[{i}]: {f.url[:100]}')
    return page


def dump_side_diagnostikk(page, side_navn):
    """Dumper DOM-info for debugging. Skrives til debug-mappe."""
    print(f'    [diag] === Diagnostikk for {side_navn} ===')

    # Frames
    print(f'    [diag] Antall frames: {len(page.frames)}')
    for i, f in enumerate(page.frames):
        print(f'    [diag]   frame[{i}]: {f.url[:120]}')

    # Søk i alle frames
    for i, frame in enumerate(page.frames):
        fname = f'frame[{i}]' if i > 0 else 'main'

        # Knapper og klikkbare elementer
        for sel_name, sel in [
            ('buttons', 'button'),
            ('visual-containers', '[class*="visual"][class*="container"]'),
            ('vcMenuBtn', '.vcMenuBtn'),
            ('more-options', '[aria-label*="options"], [aria-label*="alternativer"], [aria-label*="Options"]'),
        ]:
            try:
                count = frame.locator(sel).count()
                if count > 0:
                    print(f'    [diag]   {fname}: {count}x {sel_name}')
            except Exception:
                pass

        # Søk etter kjente tekster
        test_tekster = ['Per område', 'Over tid', 'Bydel', 'Totalpriser', 'm²-priser',
                        'Tabell', 'Graf', 'Eksporter', 'Export', 'More options',
                        'Prisutvikling', 'Omsetningstid', 'Snittpris']
        for tekst in test_tekster:
            try:
                el = frame.locator(f'text="{tekst}"')
                count = el.count()
                if count > 0:
                    vis = 'synlig' if el.first.is_visible(timeout=500) else 'skjult'
                    print(f'    [diag]   {fname}: "{tekst}" funnet ({count}x, {vis})')
            except Exception:
                pass

    # Dump synlig tekst fra hovedelementer
    try:
        all_text = page.evaluate('''() => {
            const texts = new Set();
            document.querySelectorAll('button, [role="button"], [role="tab"], [role="menuitem"]').forEach(el => {
                const t = el.textContent?.trim();
                if (t && t.length < 50) texts.add(t);
            });
            return [...texts].slice(0, 30);
        }''')
        if all_text:
            print(f'    [diag]   Klikkbare tekster i main: {all_text}')
    except Exception as e:
        print(f'    [diag]   Kunne ikke hente tekster: {e}')

    # Prøv også i alle iframes
    for i, frame in enumerate(page.frames):
        if i == 0:
            continue
        try:
            iframe_text = frame.evaluate('''() => {
                const texts = new Set();
                document.querySelectorAll('button, [role="button"], [role="tab"], [role="menuitem"], span, div').forEach(el => {
                    const t = el.textContent?.trim();
                    if (t && t.length > 2 && t.length < 40) texts.add(t);
                });
                return [...texts].slice(0, 40);
            }''')
            if iframe_text:
                print(f'    [diag]   Tekster i frame[{i}]: {iframe_text[:10]}...')  # Bare vis topp 10
        except Exception:
            pass

    print(f'    [diag] === Slutt diagnostikk ===')


def klikk_filter(page, filternavn, debug=False, timeout=3000):
    """Klikker en filterknapp i Power BI. Returnerer True hvis funnet."""
    frames_to_try = page.frames if len(page.frames) > 1 else [page]
    selektorer = [
        f'button:has-text("{filternavn}")',
        f'[role="button"]:has-text("{filternavn}")',
        f'[role="tab"]:has-text("{filternavn}")',
        f'text="{filternavn}"',
    ]
    for frame in frames_to_try:
        for sel in selektorer:
            try:
                el = frame.locator(sel).first
                if el.is_visible(timeout=timeout):
                    box = el.bounding_box()
                    if not box:
                        continue
                    if box['width'] > 500 or box['height'] > 200:
                        if debug:
                            print(f'    [debug] Filter "{filternavn}": skipper {sel} ({box["width"]:.0f}x{box["height"]:.0f} for stor)')
                        continue
                    if debug:
                        try:
                            tag = el.evaluate('e => e.tagName')
                            cls = el.evaluate('e => (e.className || "").substring(0, 60)')
                        except Exception:
                            tag, cls = '?', '?'
                        print(f'    [debug] Filter "{filternavn}": klikker {sel} → <{tag}> cls="{cls}" {box["width"]:.0f}x{box["height"]:.0f}')
                    page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    time.sleep(VENT_ETTER_FILTER)
                    return True
            except Exception:
                continue
    return False


def eksporter_visual_data(page, visual_index=0, debug=False, filformat='xlsx'):
    """Eksporterer data fra en Power BI visual via ... → Export data → Summarized data.

    Power BI viser "..." (more options) ved hover over en visual.
    visual_index: hvilken visual å eksportere fra (0 = første synlige chart).
    filformat: 'xlsx' (default) eller 'csv' — velger format i eksport-dialogen.
    Returnerer sti til nedlastet fil, eller None.
    """
    print(f'  Eksporterer data ({filformat})...')

    more_selektorer = [
        'button[aria-label="More options"]',
        'button[aria-label="Flere alternativer"]',
        'button[title="More options"]',
        'button[title="Flere alternativer"]',
        '.vcMenuBtn',
        '.visualContainerHeader button',
        'button.vcMenuBtn',
        '[data-testid="visual-more-options"]',
    ]

    visual_containere = [
        '.visual-container-component',
        '.visualContainerGroup',
        'visual-container',
        '.visualContainer',
    ]

    all_frames = page.frames if len(page.frames) > 1 else [page]

    # Samle kandidat-visuals med størrelse, sorter etter areal (størst først)
    candidates = []
    for frame in all_frames:
        for vc_sel in visual_containere:
            try:
                visuals = frame.locator(vc_sel)
                count = visuals.count()
                if count == 0:
                    continue
                if debug:
                    print(f'    [debug] Fant {count} visuals med selektor: {vc_sel}')
                for idx in range(count):
                    try:
                        v = visuals.nth(idx)
                        if not v.is_visible(timeout=500):
                            continue
                        box = v.bounding_box()
                        if not box:
                            continue
                        w, h = box['width'], box['height']
                        if w < 200 or h < 150:
                            continue
                        if w > 1600 and h > 900:
                            continue
                        candidates.append((w * h, v, frame, idx, w, h))
                    except Exception:
                        continue
            except Exception:
                continue

    # Fallback: inkluder .visualContainerHost hvis ingen andre kandidater
    if not candidates:
        for frame in all_frames:
            try:
                host = frame.locator('.visualContainerHost')
                if host.count() > 0 and host.first.is_visible(timeout=500):
                    box = host.first.bounding_box()
                    if box:
                        if debug:
                            print(f'    [debug] Fallback til .visualContainerHost: {box["width"]:.0f}x{box["height"]:.0f}')
                        candidates.append((box['width'] * box['height'], host.first, frame, 0, box['width'], box['height']))
            except Exception:
                continue

    candidates.sort(key=lambda x: x[0], reverse=True)
    if debug:
        print(f'    [debug] {len(candidates)} kandidat-visuals')
        for i, (_, _, _, idx, w, h) in enumerate(candidates[:8]):
            print(f'    [debug]   #{i}: visual {idx}, {w:.0f}x{h:.0f}')

    found_menu = False
    for _, v, frame, idx, w, h in candidates:
        if found_menu:
            break
        try:
            if debug:
                print(f'    [debug] Hover over visual {idx}: {w:.0f}x{h:.0f}')
            box = v.bounding_box()
            page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
            time.sleep(1.5)

            for btn_sel in more_selektorer:
                try:
                    btn = v.locator(btn_sel).first
                    if btn.is_visible(timeout=1500):
                        btn.click()
                        time.sleep(1)
                        found_menu = True
                        if debug:
                            print(f'    [debug] Klikket meny via: {btn_sel} (inni visual)')
                        break
                except Exception:
                    continue

            if not found_menu:
                for btn_sel in more_selektorer:
                    try:
                        btn = frame.locator(btn_sel).first
                        if btn.is_visible(timeout=1000):
                            btn.click()
                            time.sleep(1)
                            found_menu = True
                            if debug:
                                print(f'    [debug] Klikket meny via: {btn_sel} (frame-level)')
                            break
                    except Exception:
                        continue
        except Exception:
            continue

    if not found_menu:
        print('    FEIL: Kunne ikke finne "..." meny-knappen')
        if debug:
            page.screenshot(path=os.path.join(DEBUG_DIR, 'eksport_feil_meny.png'), full_page=True)
        return None

    # Kontekstmeny og eksport-dialog rendres ofte i hovedframen, prøv begge
    targets = [frame, page] if frame is not page else [page]

    # Klikk "Export data" i kontekstmenyen
    export_selektorer = [
        'button:has-text("Export data")',
        'span:has-text("Export data")',
        'button:has-text("Eksporter data")',
        'span:has-text("Eksporter data")',
        '[data-testid="export-data"]',
        'li:has-text("Export data")',
        'div[role="menuitem"]:has-text("Export")',
    ]

    found_export = False
    for target in targets:
        if found_export:
            break
        for sel in export_selektorer:
            try:
                el = target.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.click()
                    time.sleep(2)
                    found_export = True
                    if debug:
                        print(f'    [debug] Klikket export via: {sel}')
                    break
            except Exception:
                continue

    if not found_export:
        print('    FEIL: Fant ikke "Export data" i menyen')
        if debug:
            page.screenshot(path=os.path.join(DEBUG_DIR, 'eksport_feil_export.png'), full_page=True)
        return None

    # Vent på at eksport-dialogen åpner seg
    time.sleep(2)
    if debug:
        page.screenshot(path=os.path.join(DEBUG_DIR, 'eksport_dialog_opened.png'), full_page=True)

    # Velg "Oppsummerte data" i eksport-dialogen
    summarized_clicked = False
    summarized_selektorer = [
        'div[role="dialog"] >> text=Oppsummerte data',
        'text=Oppsummerte data',
        'text=Summarized data',
        ':text-is("Oppsummerte data")',
        ':text-is("Summarized data")',
    ]
    for sel in summarized_selektorer:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                summarized_clicked = True
                if debug:
                    print(f'    [debug] Klikket "Oppsummerte data" via: {sel}')
                time.sleep(1)
                break
        except Exception:
            continue

    if not summarized_clicked:
        if debug:
            print('    [debug] Kunne ikke finne "Oppsummerte data" — prøver å klikke andre kort i dialogen')
            # Dump hva som finnes i dialogen
            try:
                dialog_text = page.evaluate('''() => {
                    const dialog = document.querySelector('[role="dialog"]') ||
                                   document.querySelector('.modal') ||
                                   document.querySelector('[class*="dialog"]');
                    if (dialog) return dialog.textContent?.substring(0, 500);
                    return "Ingen dialog funnet i DOM";
                }''')
                print(f'    [debug] Dialog-innhold: {dialog_text}')
            except Exception:
                pass

    # Velg CSV-format hvis bedt om det. PBI-dialogen har et format-valg
    # (dropdown eller radio) som default står på XLSX.
    if filformat == 'csv':
        csv_valgt = False
        csv_selektorer = [
            'div[role="dialog"] input[type="radio"][value*="csv" i]',
            'div[role="dialog"] input[type="radio"][value*="Csv"]',
            'div[role="dialog"] label:has-text(".csv")',
            'div[role="dialog"] label:has-text("CSV")',
            'div[role="dialog"] >> text=/\\.csv/i',
            'div[role="dialog"] >> text=CSV (kommadelt)',
            'div[role="dialog"] >> text=Comma separated',
            'label:has-text(".csv")',
            'label:has-text("CSV")',
        ]
        for sel in csv_selektorer:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    csv_valgt = True
                    if debug:
                        print(f'    [debug] Valgt CSV-format via: {sel}')
                    time.sleep(0.5)
                    break
            except Exception:
                continue

        # Fallback: åpne eventuell format-dropdown og velg CSV
        if not csv_valgt:
            dropdown_selektorer = [
                'div[role="dialog"] [role="combobox"]',
                'div[role="dialog"] select',
                'div[role="dialog"] button:has-text(".xlsx")',
                'div[role="dialog"] button:has-text("Excel")',
            ]
            for ddsel in dropdown_selektorer:
                try:
                    dd = page.locator(ddsel).first
                    if dd.is_visible(timeout=1500):
                        dd.click()
                        time.sleep(0.5)
                        for opt_sel in [
                            'div[role="option"]:has-text(".csv")',
                            'div[role="option"]:has-text("CSV")',
                            'li:has-text(".csv")',
                            ':text-is(".csv")',
                        ]:
                            try:
                                opt = page.locator(opt_sel).first
                                if opt.is_visible(timeout=1500):
                                    opt.click()
                                    csv_valgt = True
                                    if debug:
                                        print(f'    [debug] Valgt CSV via dropdown {ddsel} → {opt_sel}')
                                    time.sleep(0.5)
                                    break
                            except Exception:
                                continue
                        if csv_valgt:
                            break
                except Exception:
                    continue

        if not csv_valgt:
            print('    ADVARSEL: Kunne ikke velge CSV-format — fortsetter med default (sannsynligvis XLSX).')
            if debug:
                try:
                    dialog_html = page.evaluate('''() => {
                        const d = document.querySelector('[role="dialog"]');
                        return d ? d.outerHTML.substring(0, 2000) : 'ingen dialog';
                    }''')
                    print(f'    [debug] Dialog HTML: {dialog_html}')
                except Exception:
                    pass

    if debug:
        page.screenshot(path=os.path.join(DEBUG_DIR, 'eksport_dialog_selected.png'), full_page=True)

    # Klikk Export-knappen i dialogen og vent på nedlasting
    # Bruk eksakt klasse-selektor for dialog-knappen (ikke toolbar-"Eksporter")
    try:
        with page.expect_download(timeout=30000) as download_info:
            # Primær: bruk klasse-selektor fra Power BI dialog
            export_btn = page.locator('button.primaryBtn.exportButton')
            if export_btn.count() > 0 and export_btn.first.is_visible(timeout=3000):
                if debug:
                    print('    [debug] Klikker dialog-eksport via: button.primaryBtn.exportButton')
                export_btn.first.click()
            else:
                # Fallback: prøv andre selektorer, men scope til dialog-kontekst
                fallback_selektorer = [
                    'button.exportButton:has-text("Eksporter")',
                    'button.exportButton:has-text("Eksportere")',
                    'button.exportButton:has-text("Export")',
                ]
                clicked = False
                for sel in fallback_selektorer:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=2000):
                            if debug:
                                print(f'    [debug] Klikker dialog-eksport via: {sel}')
                            btn.click()
                            clicked = True
                            break
                    except Exception:
                        continue

                if not clicked:
                    if debug:
                        print('    [debug] Kunne ikke finne eksport-knapp, dumper synlige knapper:')
                        try:
                            all_btns = page.evaluate('''() => {
                                return [...document.querySelectorAll('button')].map(b => ({
                                    text: b.textContent?.trim()?.substring(0, 50),
                                    cls: b.className?.substring(0, 80),
                                    visible: b.offsetParent !== null
                                })).filter(b => b.visible);
                            }''')
                            for b in all_btns:
                                print(f'    [debug]   knapp: "{b["text"]}" class="{b["cls"]}"')
                        except Exception:
                            pass
                    print('    FEIL: Kunne ikke klikke eksport-knappen i dialogen')

        download = download_info.value
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        dest = os.path.join(DOWNLOAD_DIR, download.suggested_filename or f'export_{int(time.time())}.{filformat}')
        download.save_as(dest)
        print(f'    Lastet ned: {dest}')
        return dest

    except Exception as e:
        print(f'    FEIL ved nedlasting: {e}')
        if debug:
            page.screenshot(path=os.path.join(DEBUG_DIR, 'eksport_feil_download.png'), full_page=True)
        return None


# === SIDE-SCRAPERE ===

def scrape_side(page, side_navn, filtre, debug=False):
    """Navigerer til en side, setter filtre, og eksporterer data."""
    side = SIDER[side_navn]
    url = pbi_url(side['reportPage'], side.get('bookmark'))

    print(f'\n--- {side_navn.replace("_", " ").title()} ---')
    print(f'  Navigerer til {side["reportPage"][:30]}...')
    if side.get('bookmark'):
        print(f'  Bruker bookmark {side["bookmark"][:20]}...')

    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    time.sleep(VENT_ETTER_NAVIGERING)

    if debug:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(DEBUG_DIR, f'{side_navn}_01_loaded.png'), full_page=True)
        dump_side_diagnostikk(page, side_navn)

    # Klikk filtre
    for filternavn in filtre:
        ok = klikk_filter(page, filternavn, debug=debug)
        if debug and not ok:
            print(f'    [debug] Filter "{filternavn}": IKKE FUNNET')

    # Vent litt ekstra etter filtrering for at Power BI skal rendere ny visning
    if filtre:
        time.sleep(5)

    if debug:
        page.screenshot(path=os.path.join(DEBUG_DIR, f'{side_navn}_02_filtered.png'), full_page=True)

    # Eksporter data
    xlsx_fil = eksporter_visual_data(page, debug=debug)
    if xlsx_fil:
        data, oslo_total = parse_xlsx(xlsx_fil)
        felt = side['felt']
        print(f'  Resultat ({felt}): {len(data)} bydeler')
        for bid, val in sorted(data.items()):
            print(f'    {OSLO_BYDELER.get(bid, bid)}: {val}')
        return data, oslo_total

    print('  Ingen data eksportert')
    return {}, None


def scrape_timeseries_side(page, side_navn, filtre=None, debug=False):
    """Navigerer til en side (evt. via bookmark), eksporterer, og parser som tidsserie.

    Returnerer (dict[bydel_id] -> [entry, ...], oslo_series).
    """
    side = SIDER[side_navn]
    kind = side.get('timeseries', 'monthly')
    url = pbi_url(side['reportPage'], side.get('bookmark'), side.get('visual'))

    print(f'\n--- {side_navn.replace("_", " ").title()} (tidsserie/{kind}) ---')
    print(f'  Navigerer til {side["reportPage"][:30]}...')
    if side.get('visual'):
        print(f'  Fokusmodus på visual {side["visual"][:20]}...')
    if side.get('bookmark'):
        print(f'  Bruker bookmark {side["bookmark"][:20]}...')

    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    time.sleep(VENT_ETTER_NAVIGERING)

    if debug:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(DEBUG_DIR, f'{side_navn}_01_loaded.png'), full_page=True)

    for filternavn in (filtre or []):
        ok = klikk_filter(page, filternavn, debug=debug)
        if debug and not ok:
            print(f'    [debug] Filter "{filternavn}": IKKE FUNNET')
    if filtre:
        time.sleep(5)

    if debug:
        page.screenshot(path=os.path.join(DEBUG_DIR, f'{side_navn}_02_filtered.png'), full_page=True)

    fil = eksporter_visual_data(page, debug=debug, filformat='csv')
    if not fil:
        print('  Ingen data eksportert')
        return {}, []

    if fil.lower().endswith('.csv'):
        per_bydel, oslo_series = parse_csv_timeseries(fil, kind=kind)
    else:
        per_bydel, oslo_series = parse_xlsx_timeseries(fil, kind=kind)
    felt = side['felt']
    print(f'  Resultat ({felt}): {len(per_bydel)} bydeler, {len(oslo_series)} Oslo-punkter')
    return per_bydel, oslo_series


def scrape_snittpris_m2(page, debug=False):
    """Klikker m²-priser tab på snittpris-siden (allerede navigert dit)."""
    print('\n--- Snittpris M2 ---')

    for tab in ['m²-priser', 'm2-priser']:
        if klikk_filter(page, tab, debug=debug):
            break

    klikk_filter(page, 'Per område', debug=debug)
    klikk_filter(page, 'Bydel', debug=debug)
    time.sleep(5)

    if debug:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        page.screenshot(path=os.path.join(DEBUG_DIR, 'snittpris_m2_filtered.png'), full_page=True)

    xlsx_fil = eksporter_visual_data(page, debug=debug)
    if xlsx_fil:
        data, oslo_total = parse_xlsx(xlsx_fil)
        print(f'  Resultat (pricePerSqm): {len(data)} bydeler')
        for bid, val in sorted(data.items()):
            print(f'    {OSLO_BYDELER.get(bid, bid)}: {val:,.0f} kr/m²')
        return data, oslo_total

    print('  Ingen data eksportert')
    return {}, None


# === DATA-SAMLING ===

def assembler_resultat(prisutvikling, omsetningstid, snittpris_total, snittpris_m2,
                       oslo_pris=None, oslo_omset=None, oslo_snitt=None, oslo_m2=None,
                       sales_per_month=None, listings_per_month=None,
                       price_index=None, oslo_price_index=None,
                       existing=None):
    """Bygger bydel_statistikk.json-struktur.

    `existing` er evt. forrige JSON — brukes for å beholde felter som ikke ble scrapet
    i dette kjøringen (delvis scrape med --page).
    """
    oslo_fallback = {
        'priceChange': oslo_pris,
        'avgDaysOnMarket': oslo_omset,
        'medianPrice': oslo_snitt,
        'pricePerSqm': oslo_m2,
    }

    existing_by_id = {}
    if existing and isinstance(existing.get('bydeler'), list):
        for b in existing['bydeler']:
            if b.get('id'):
                existing_by_id[b['id']] = b

    sales_per_month = sales_per_month or {}
    listings_per_month = listings_per_month or {}
    price_index = price_index or {}

    bydeler = []
    for bydel_id, bydel_navn in OSLO_BYDELER.items():
        prev = existing_by_id.get(bydel_id, {})
        entry = {
            'id': bydel_id,
            'name': bydel_navn,
            'priceChange': prisutvikling.get(bydel_id, prev.get('priceChange')),
            'avgDaysOnMarket': omsetningstid.get(bydel_id, prev.get('avgDaysOnMarket')),
            'medianPrice': snittpris_total.get(bydel_id, prev.get('medianPrice')),
            'pricePerSqm': snittpris_m2.get(bydel_id, prev.get('pricePerSqm')),
            'salesPerMonth': sales_per_month.get(bydel_id, prev.get('salesPerMonth')),
            'listingsPerMonth': listings_per_month.get(bydel_id, prev.get('listingsPerMonth')),
            'priceIndex': price_index.get(bydel_id, prev.get('priceIndex')),
        }
        if bydel_id == 'sentrum':
            sentrum_fallback = dict(oslo_fallback)
            sentrum_fallback['priceIndex'] = oslo_price_index or None
            for felt, fallback in sentrum_fallback.items():
                if entry[felt] is None and fallback:
                    entry[felt] = fallback
        skalar_felt = ['priceChange', 'avgDaysOnMarket', 'medianPrice', 'pricePerSqm']
        mangler = [k for k in skalar_felt if entry[k] is None]
        if mangler:
            print(f'  ADVARSEL: {bydel_navn} mangler: {", ".join(mangler)}')
        bydeler.append(entry)

    prev_oslo = existing.get('oslo_totalt', {}) if existing else {}
    oslo_totalt = {
        'priceChange': oslo_pris if oslo_pris is not None else prev_oslo.get('priceChange'),
        'avgDaysOnMarket': oslo_omset if oslo_omset is not None else prev_oslo.get('avgDaysOnMarket'),
        'medianPrice': oslo_snitt if oslo_snitt is not None else prev_oslo.get('medianPrice'),
        'pricePerSqm': oslo_m2 if oslo_m2 is not None else prev_oslo.get('pricePerSqm'),
        'priceIndex': oslo_price_index if oslo_price_index else prev_oslo.get('priceIndex'),
    }
    for felt in ['priceChange', 'avgDaysOnMarket', 'medianPrice', 'pricePerSqm']:
        if oslo_totalt[felt] is None:
            verdier = [b[felt] for b in bydeler if b[felt] is not None]
            if verdier:
                oslo_totalt[felt] = round(sum(verdier) / len(verdier), 1)

    return {
        'scraped_at': datetime.now().isoformat(timespec='seconds'),
        'oslo_totalt': oslo_totalt,
        'bydeler': bydeler,
    }


def skriv_json(data, filsti=OUTPUT_JSON):
    os.makedirs(os.path.dirname(filsti), exist_ok=True)
    tmp = filsti + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, filsti)
    print(f'\n  Skrevet: {filsti}')


# === HOVEDFLYT ===

def main():
    parser = argparse.ArgumentParser(description='Scrape EV Innsikt for bydel-statistikk')
    parser.add_argument('--debug', action='store_true', help='Lagre screenshots')
    parser.add_argument('--page', choices=list(SIDER.keys()),
                        help='Scrape kun én spesifikk side')
    parser.add_argument('--only', help='Komma-separert liste av sider å scrape (overstyrer default).')
    args = parser.parse_args()

    for d in [OUTPUT_DIR, DOWNLOAD_DIR]:
        os.makedirs(d, exist_ok=True)
    if args.debug:
        os.makedirs(DEBUG_DIR, exist_ok=True)

    print('=' * 60)
    print('  EV Innsikt — Bydel-statistikk scraper (xlsx-eksport)')
    print('=' * 60)

    with sync_playwright() as pw:
        browser, context = lag_browser_og_context(pw)
        page = context.new_page()

        # Naviger til rapport
        foerste = args.page or 'prisutvikling'
        print(f'\n  Navigerer til Power BI...')
        page.goto(pbi_url(SIDER[foerste]['reportPage']), wait_until='domcontentloaded', timeout=60000)
        time.sleep(VENT_ETTER_NAVIGERING)

        if not er_pbi_innlogget(page):
            print('\n  FEIL: Dia-sesjonen er utløpt eller mangler.')
            print('  Logg inn på Power BI i Dia og kjør scriptet på nytt.')
            browser.close()
            sys.exit(1)

        print('  Innlogget via Dia-cookies.')

        # Scrape
        prisutvikling = {}
        omsetningstid = {}
        snittpris_total = {}
        snittpris_m2_data = {}
        sales_per_month = {}
        listings_per_month = {}
        price_index = {}
        oslo_pris = oslo_omset = oslo_snitt = oslo_m2 = None
        oslo_price_index = []

        default_sider = [
            'prisutvikling', 'omsetningstid', 'snittpris', 'snittpris_m2',
            'antall_solgt', 'antall_til_salgs', 'prisindeks',
        ]
        if args.page:
            sider = [args.page]
        elif args.only:
            sider = [s.strip() for s in args.only.split(',') if s.strip()]
        else:
            sider = default_sider

        # Last inn eksisterende JSON så delvis scrape bevarer felter vi ikke rørte
        existing = None
        if os.path.exists(OUTPUT_JSON):
            try:
                with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception as e:
                print(f'  Advarsel: Kunne ikke lese eksisterende {OUTPUT_JSON}: {e}')

        for side in sider:
            if _stopp:
                break

            if side == 'prisutvikling':
                data, oslo_val = scrape_side(page, 'prisutvikling',
                    [],
                    debug=args.debug)
                prisutvikling = data
                oslo_pris = oslo_val

            elif side == 'omsetningstid':
                data, oslo_val = scrape_side(page, 'omsetningstid',
                    ['Per område', 'Bydel'],
                    debug=args.debug)
                omsetningstid = data
                oslo_omset = oslo_val

            elif side == 'snittpris':
                data, oslo_val = scrape_side(page, 'snittpris',
                    ['Totalpriser', 'Per område', 'Bydel'],
                    debug=args.debug)
                snittpris_total = data
                oslo_snitt = oslo_val

            elif side == 'snittpris_m2':
                if 'snittpris' in sider and sider.index('snittpris_m2') == sider.index('snittpris') + 1:
                    data, oslo_val = scrape_snittpris_m2(page, debug=args.debug)
                else:
                    data, oslo_val = scrape_side(page, 'snittpris_m2',
                        ['m²-priser', 'Per område', 'Bydel'],
                        debug=args.debug)
                snittpris_m2_data = data
                oslo_m2 = oslo_val

            elif side == 'antall_solgt':
                data, _ = scrape_timeseries_side(page, 'antall_solgt', debug=args.debug)
                sales_per_month = data

            elif side == 'antall_til_salgs':
                data, _ = scrape_timeseries_side(page, 'antall_til_salgs', debug=args.debug)
                listings_per_month = data

            elif side == 'prisindeks':
                data, oslo_pi = scrape_timeseries_side(page, 'prisindeks', debug=args.debug)
                price_index = data
                oslo_price_index = oslo_pi

            if side != sider[-1]:
                neste = sider[sider.index(side) + 1]
                samme_side = (
                    SIDER.get(side, {}).get('reportPage') == SIDER.get(neste, {}).get('reportPage')
                    and SIDER.get(side, {}).get('bookmark') == SIDER.get(neste, {}).get('bookmark')
                )
                if not samme_side:
                    print(f'\n  Venter {VENTETID_MELLOM_SIDER}s...')
                    time.sleep(VENTETID_MELLOM_SIDER)

        # Assembler
        resultat = assembler_resultat(
            prisutvikling, omsetningstid, snittpris_total, snittpris_m2_data,
            oslo_pris, oslo_omset, oslo_snitt, oslo_m2,
            sales_per_month=sales_per_month,
            listings_per_month=listings_per_month,
            price_index=price_index,
            oslo_price_index=oslo_price_index,
            existing=existing,
        )
        skriv_json(resultat)

        bydeler_ok = sum(1 for b in resultat['bydeler']
                         if all(b.get(f) is not None for f in ['priceChange', 'avgDaysOnMarket', 'medianPrice', 'pricePerSqm']))
        print(f'\n  Ferdig! {bydeler_ok}/{len(OSLO_BYDELER)} bydeler med komplett data.')

        if bydeler_ok < 8 and not args.page:
            print('\n  *** ADVARSEL: Færre enn 8 bydeler med komplett data! ***')
            print('  Kjør med --debug for å inspisere screenshots.')
            browser.close()
            sys.exit(2)

        browser.close()


if __name__ == '__main__':
    main()
