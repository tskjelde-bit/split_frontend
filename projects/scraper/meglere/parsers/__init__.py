"""Parser-registry per kjede.

Hver parser-modul eksporterer:
  parse(html, page, kontor_navn, kontor_url) -> list[dict]
  pre_load(page, url) -> None     # site-spesifikk venting/scrolling før HTML-capture
"""

from . import (
    em1, privatmegleren, dnb, nordvik, partners, eie,
    emera, mekleriet, boa, aktiv, sem_johnsen,
)


PARSERS = {
    "EM1": em1,
    "PrivatMegleren": privatmegleren,
    "DNB": dnb,
    "Nordvik": nordvik,
    "Schala & Partners": partners,
    "Eie": eie,
    "Emera": emera,
    "Mekleriet": mekleriet,
    "Boa": boa,
    "Aktiv": aktiv,
    "Sem & Johnsen": sem_johnsen,
}


CLI_ALIAS = {
    "em1": "EM1",
    "privatmegleren": "PrivatMegleren",
    "dnb": "DNB",
    "nordvik": "Nordvik",
    "partners": "Schala & Partners",
    "eie": "Eie",
    "emera": "Emera",
    "mekleriet": "Mekleriet",
    "boa": "Boa",
    "aktiv": "Aktiv",
    "semjohnsen": "Sem & Johnsen",
    "sem-johnsen": "Sem & Johnsen",
    "generelle": "Generelle",
}


# For "Generelle"-kjeden: dispatch til riktig parser-modul basert på URL-domene.
# Records får kjede="Generelle" i output (overstyres av orchestrator).
GENERELLE_DOMENE_PARSER = {
    "nordvikbolig.no": nordvik,
    "privatmegleren.no": privatmegleren,
    "aktiv.no": aktiv,
    "dnbeiendom.no": dnb,
}
