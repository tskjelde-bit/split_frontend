"""EiendomsMegler 1 — eiendomsmegler1.no/kontor/<slug>"""

from ._common import extract_persons_heuristic


def parse(html, page, kontor_navn, kontor_url):
    return extract_persons_heuristic(html, "EM1", kontor_navn, kontor_url)


def pre_load(page, url):
    """Hook for site-spesifikk venting/scrolling før HTML-capture. Server-rendret,
    så ingenting å gjøre."""
    return
