"""Nordvik Bolig — nordvikbolig.no/kontorer/<slug>

Personlisten ligger i __NEXT_DATA__-JSON som strukturerte Employee-objekter.
Mye mer pålitelig enn DOM-skraping.
"""

import json

from bs4 import BeautifulSoup

from ._common import (
    formater_telefon,
    normaliser_telefon,
    splitt_navn,
)


def _walk_for_employees(obj):
    if isinstance(obj, dict):
        if obj.get("__typename") == "Employee":
            yield obj
        for v in obj.values():
            yield from _walk_for_employees(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_for_employees(v)


def parse(html, page, kontor_navn, kontor_url):
    soup = BeautifulSoup(html, "lxml")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return []

    try:
        data = json.loads(script.string)
    except json.JSONDecodeError:
        return []

    ansatte = []
    seen = set()

    for emp in _walk_for_employees(data):
        navn = (emp.get("name") or "").strip()
        if not navn:
            continue

        rolle = (emp.get("title") or "").strip()
        epost = (emp.get("email") or "").strip()
        raa_tlf = emp.get("mobilePhone") or emp.get("phone") or ""

        telefon = formater_telefon(raa_tlf)
        telefon_norm = normaliser_telefon(raa_tlf)
        fornavn, etternavn = splitt_navn(navn)

        nokkel = (navn.lower(), telefon_norm, epost.lower())
        if nokkel in seen:
            continue
        seen.add(nokkel)

        ansatte.append({
            "kjede": "Nordvik",
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


def pre_load(page, url):
    return
