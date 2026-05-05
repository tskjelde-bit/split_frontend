"""Mekleriet — mekleriet.no/vare-meglere/<slug>

Server-rendret. Hver person har <h5 class="broker-name">Navn</h5> + tel: + mailto:.
Markupen er duplisert (desktop/mobile-versjoner) — derfor dedup på (navn, tel, e-post).
Noen h5-varianter har <br/> midt i navnet ("Ole Anders<br/>Teslo") — vi normaliserer.
"""

import re

from bs4 import BeautifulSoup

from ._common import (
    formater_telefon,
    normaliser_telefon,
    splitt_navn,
)


def parse(html, page, kontor_navn, kontor_url):
    soup = BeautifulSoup(html, "lxml")

    ansatte = []
    seen = set()

    for h5 in soup.find_all("h5", class_=re.compile(r"broker-name")):
        # Normaliser whitespace (h5 med <br/> blir "Ole Anders\nTeslo")
        navn = " ".join(h5.get_text(" ", strip=True).split())
        if not navn or " " not in navn:
            continue

        # Gå opp til kortet (ancestor som har både navn-h5 og tel-anchor)
        kort = h5.parent
        for _ in range(6):
            if kort is None or kort.name in (None, "html", "body"):
                break
            if kort.find("a", href=re.compile(r"^tel:")):
                break
            kort = kort.parent
        if kort is None:
            continue

        # Rolle: første <p> i kortet som ikke er kontornavn / kontaktlenke
        rolle = ""
        for p in kort.find_all(["p"]):
            tekst = p.get_text(" ", strip=True)
            if not tekst:
                continue
            if "@" in tekst or re.search(r"\+?\d[\d\s]{5,}", tekst):
                continue
            if tekst.lower() in {"kontakt meg", kontor_navn.lower()}:
                continue
            if tekst.startswith("Mekleriet "):
                continue
            rolle = tekst
            break

        telefon = ""
        telefon_norm = ""
        tel_el = kort.find("a", href=re.compile(r"^tel:"))
        if tel_el:
            raa = tel_el.get("href", "").replace("tel:", "")
            telefon = formater_telefon(raa)
            telefon_norm = normaliser_telefon(raa)

        epost = ""
        mail_el = kort.find("a", href=re.compile(r"^mailto:"))
        if mail_el:
            epost = mail_el.get("href", "").replace("mailto:", "").split("?")[0].strip()

        fornavn, etternavn = splitt_navn(navn)
        nokkel = (navn.lower(), telefon_norm, epost.lower())
        if nokkel in seen:
            continue
        seen.add(nokkel)

        ansatte.append({
            "kjede": "Mekleriet",
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
