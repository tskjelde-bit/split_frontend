"""Schala & Partners — partners.no/kontor/<slug>

JS-rendret. Trenger venting + scroll før innhold er i DOM.
"""

import time

from ._common import extract_persons_heuristic


def parse(html, page, kontor_navn, kontor_url):
    return extract_persons_heuristic(html, "Schala & Partners", kontor_navn, kontor_url)


def pre_load(page, url):
    """Vent til person-kort er i DOM. Selektor verifiseres ved første kjøring; vi
    bruker tel:-anchor som universell markør (enhver person-kort vil ha en)."""
    try:
        page.wait_for_selector('a[href^="tel:"]', timeout=15000)
    except Exception:
        pass
    _scroll_til_bunn(page)


def _scroll_til_bunn(page, maks_steg=12):
    forrige = 0
    for _ in range(maks_steg):
        try:
            page.mouse.wheel(0, 1500)
            time.sleep(0.6)
            hoyde = page.evaluate("document.body.scrollHeight")
            if hoyde == forrige:
                break
            forrige = hoyde
        except Exception:
            break
