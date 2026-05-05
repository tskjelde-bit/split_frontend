"""Sem & Johnsen — sem-johnsen.no/kontaktoss#<seksjon>

Alle 4 "kontorer" peker til samme side med ulike URL-fragmenter:
  #eiendomsmeglere, #prosjektmeglere, #fag-og-meglerstøtte, #administrasjon

Strukturen er JS-rendret (Next.js + Sanity CMS). Markup-mønster:

  <span>Eiendomsmeglere</span>      ← seksjon-overskrift (ikke h-tag!)
  <ul class="col-span-full layout">
    <li class="list-quarter ...">
      <a href="/meglere/<slug>" title="...">...</a>
      <div class="ml-2">
        <p class="...font-medium...">Aurora Solbakk Andersen</p>   ← navn
        <p class="...font-light...">Eiendomsmegler/Partner</p>     ← rolle
        <a href="tel:+47...">...</a>
        <a href="mailto:...">...</a>
      </div>
    </li>
    ...
  </ul>
"""

import re
import time
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup

from ._common import (
    formater_telefon,
    normaliser_telefon,
    splitt_navn,
)


# Fragment i URL → index av ul.col-span-full.layout-blokken på siden
# (rekkefølgen på siden er: Eiendomsmeglere, Prosjektmeglere, Fag og
# meglerstøtte, Administrasjon). Header-spans øverst er nav-lenker som peker
# til samme seksjon — kan ikke brukes direkte til DOM-match.
_FRAGMENT_TIL_INDEX = {
    "eiendomsmeglere": 0,
    "prosjektmeglere": 1,
    "fag-og-meglerstøtte": 2,
    "fag-og-meglerstotte": 2,
    "administrasjon": 3,
}


def parse(html, page, kontor_navn, kontor_url):
    fragment = unquote(urlparse(kontor_url).fragment).lower()
    idx = _FRAGMENT_TIL_INDEX.get(fragment)

    soup = BeautifulSoup(html, "lxml")
    uls = soup.select("ul.col-span-full.layout")

    if idx is None or idx >= len(uls):
        return []

    return _parse_ul(uls[idx], kontor_navn, kontor_url)


def _parse_ul(ul, kontor_navn, kontor_url):
    ansatte = []
    seen = set()

    for li in ul.find_all("li", recursive=False):
        # Navn: enten første <p class*="font-medium"> eller fra <a title="...">
        navn = _hent_navn(li)
        if not navn:
            continue

        # Rolle: første <p> som ikke er navnet
        rolle = ""
        for p in li.find_all("p"):
            tekst = p.get_text(" ", strip=True)
            if not tekst or tekst == navn:
                continue
            if "@" in tekst or re.search(r"\+?\d[\d\s]{5,}", tekst):
                continue
            rolle = tekst
            break

        # Telefon
        telefon = ""
        telefon_norm = ""
        tel_el = li.find("a", href=re.compile(r"^tel:"))
        if tel_el:
            raa = tel_el.get("href", "").replace("tel:", "")
            telefon = formater_telefon(raa)
            telefon_norm = normaliser_telefon(raa)

        # E-post
        epost = ""
        mail_el = li.find("a", href=re.compile(r"^mailto:"))
        if mail_el:
            epost = mail_el.get("href", "").replace("mailto:", "").split("?")[0].strip()

        fornavn, etternavn = splitt_navn(navn)
        nokkel = (navn.lower(), telefon_norm, epost.lower())
        if nokkel in seen:
            continue
        seen.add(nokkel)

        ansatte.append({
            "kjede": "Sem & Johnsen",
            "kontor": kontor_navn,
            "kontor_url": kontor_url,
            "fornavn": fornavn,
            "etternavn": etternavn,
            "fullt_navn": navn,
            "rolle": rolle,
            "telefon": telefon,
            "telefon_normalisert": telefon_norm,
            "epost": epost,
        })

    return ansatte


def _hent_navn(li):
    # 1. <p class*="font-medium"> — den vanlige navne-stilen
    for p in li.find_all("p"):
        klasser = " ".join(p.get("class") or [])
        if "font-medium" in klasser:
            tekst = p.get_text(" ", strip=True)
            if tekst and " " in tekst:
                return tekst

    # 2. Fall tilbake til title-attr på første /meglere/<slug>-anchor
    a = li.find("a", href=re.compile(r"^/meglere/[^/]+/?$"))
    if a is not None:
        navn = a.get("title", "").strip()
        if navn and " " in navn:
            return navn
        sr = a.find("span", class_="sr-only")
        if sr:
            tekst = sr.get_text(strip=True)
            if tekst and " " in tekst:
                return tekst

    return ""


def pre_load(page, url):
    try:
        page.wait_for_selector('a[href^="tel:"]', timeout=20000)
    except Exception:
        pass
    _scroll_til_bunn(page)
    # Ekstra vent for at hele listen skal være rendret
    try:
        page.wait_for_function(
            "document.querySelectorAll('ul.col-span-full a[href^=\"tel:\"]').length > 5",
            timeout=10000,
        )
    except Exception:
        pass


def _scroll_til_bunn(page, maks_steg=25):
    forrige = 0
    for _ in range(maks_steg):
        try:
            page.mouse.wheel(0, 1500)
            time.sleep(0.5)
            hoyde = page.evaluate("document.body.scrollHeight")
            if hoyde == forrige:
                break
            forrige = hoyde
        except Exception:
            break
