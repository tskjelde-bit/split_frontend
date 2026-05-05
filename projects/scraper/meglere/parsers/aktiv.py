"""Aktiv Eiendomsmegling — aktiv.no/om-aktiv/vare-kontorer/<slug>

JS-rendret SPA. Trenger venting + scrolling før personlisten dukker opp.
Faller tilbake på heuristikken når kortet er rendret.
"""

import time

from ._common import extract_persons_heuristic


def parse(html, page, kontor_navn, kontor_url):
    return extract_persons_heuristic(html, "Aktiv", kontor_navn, kontor_url)


def pre_load(page, url):
    # Vent til personlisten har lastet — vi bruker tel:-anchor som markør
    # (sidens "Kontakt oss"-seksjon har én, men personlistens kommer etter
    # at JS har kjørt). Så vi venter litt ekstra etter første tel-treff.
    try:
        page.wait_for_selector('a[href^="tel:"]', timeout=20000)
    except Exception:
        pass
    _scroll_til_bunn(page)
    # Ekstra vent for at meglere-seksjonen skal renderes
    try:
        page.wait_for_function(
            "document.querySelectorAll('a[href^=\"tel:\"]').length > 1",
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
