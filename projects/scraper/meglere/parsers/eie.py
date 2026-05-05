"""EIE Eiendomsmegling — eie.no/eiendom/kontorer/<slug>

JS-rendret. Trenger venting + scroll.
"""

import time

from ._common import extract_persons_heuristic


def parse(html, page, kontor_navn, kontor_url):
    return extract_persons_heuristic(html, "EIE", kontor_navn, kontor_url)


def pre_load(page, url):
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
