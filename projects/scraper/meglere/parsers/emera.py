"""Emera Eiendomsmegling — emeraeiendomsmegling.no/kontorer/<slug>

Server-rendret. Hver person har <h3>Navn</h3> + <a href="/megler/<slug>">. Ingen
e-post i listen — bare på personprofilen.
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

    # Hver megler har en <a href="/megler/<slug>"> hvor h3 inni er navnet
    for a in soup.find_all("a", href=re.compile(r"^/megler/[^/]+/?$")):
        # Finn h3 i ankeret eller i nær slekt (kortet rundt)
        h3 = a.find("h3")
        if h3 is None:
            # gå opp og søk h3 i kortet
            kort = a.parent
            for _ in range(4):
                if kort is None or kort.name in (None, "html", "body"):
                    break
                h3 = kort.find("h3")
                if h3:
                    break
                kort = kort.parent
        if h3 is None:
            continue

        navn = h3.get_text(" ", strip=True)
        if not navn or " " not in navn:
            continue

        # Finn kortets felles forelder for navn + tel + rolle
        kort = h3
        for _ in range(6):
            if kort.parent is None or kort.parent.name in (None, "html", "body"):
                break
            kort = kort.parent
            if kort.find("a", href=re.compile(r"^tel:")):
                break

        rolle = ""
        for p in kort.find_all(["p", "span"]):
            tekst = p.get_text(" ", strip=True)
            if not tekst or tekst == navn:
                continue
            if "@" in tekst or re.search(r"\+?\d[\d\s]{5,}", tekst):
                continue
            if tekst.lower() in {"avtal møte", "kontakt meg", "se profil", "om megler"}:
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
            "kjede": "Emera",
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
