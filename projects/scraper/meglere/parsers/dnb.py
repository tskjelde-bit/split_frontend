"""DNB Eiendom — dnbeiendom.no/Finn-Eiendomsmegler/Oslo/<kontor>/"""

from ._common import extract_persons_heuristic


def parse(html, page, kontor_navn, kontor_url):
    return extract_persons_heuristic(html, "DNB", kontor_navn, kontor_url)


def pre_load(page, url):
    return
