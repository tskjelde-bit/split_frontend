"""Boa Eiendom — boaeiendom.no/kontakt-oss#<seksjon>

Alle 3 "kontorer" peker til samme side med ulike URL-fragmenter
(#oslo-ost, #oslo-vest, #administrasjon). Hver kjøring scraper kun ansatte
fra fragmentets seksjon. JS-rendret SPA.
"""

import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ._common import extract_persons_heuristic


def parse(html, page, kontor_navn, kontor_url):
    fragment = urlparse(kontor_url).fragment.lower()  # "oslo-ost" / "oslo-vest" / "administrasjon"

    soup = BeautifulSoup(html, "lxml")

    # Forsøk å isolere seksjonen som matcher fragmentet
    seksjon_html = _finn_seksjon_html(soup, fragment, kontor_navn)
    if seksjon_html is None:
        # Fallback: parse hele siden — bedre enn ingenting, men gir duplikater
        # på tvers av Boa-kontorene som må dedupes manuelt
        return extract_persons_heuristic(html, "Boa", kontor_navn, kontor_url)

    return extract_persons_heuristic(seksjon_html, "Boa", kontor_navn, kontor_url)


def _finn_seksjon_html(soup, fragment, kontor_navn):
    """Finn HTML-utdraget for en kontor-seksjon. Tre strategier i rekkefølge."""
    if not fragment:
        return None

    # 1. Direkte id-match
    el = soup.find(id=fragment)
    if el is not None:
        return str(el)

    # 2. Heading-match: et h2/h3/h4 hvis tekst matcher kontor_navn eller fragmentet
    fragment_ord = set(fragment.replace("-", " ").split())
    kontor_ord = set(kontor_navn.lower().replace("-", " ").split())
    soke_ord = fragment_ord | kontor_ord

    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        h_ord = set(h.get_text(strip=True).lower().replace("-", " ").split())
        if soke_ord & h_ord:
            # Ta alt mellom denne heading og neste h-tag på samme nivå
            return _utdrag_etter_heading(h)

    return None


def _utdrag_etter_heading(heading):
    h_niva = heading.name  # 'h2', 'h3', etc.
    deler = [str(heading)]
    for sib in heading.find_all_next():
        # Stopp ved neste heading på samme eller høyere nivå
        if sib.name in {"h1", "h2", "h3", "h4"}:
            if sib.name <= h_niva:  # h2 <= h2 stopper, h3 < h2 stopper
                break
        deler.append(str(sib))
        if len(deler) > 200:  # safeguard
            break
    return "".join(deler)


def pre_load(page, url):
    try:
        page.wait_for_selector('a[href^="tel:"]', timeout=20000)
    except Exception:
        pass
    _scroll_til_bunn(page)
    try:
        page.wait_for_function(
            "document.querySelectorAll('a[href^=\"tel:\"]').length > 2",
            timeout=10000,
        )
    except Exception:
        pass


def _scroll_til_bunn(page, maks_steg=15):
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
