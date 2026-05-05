"""PrivatMegleren — privatmegleren.no/<kontor-slug>

Person-kort har <a class="... name" href="/megler/<slug>">Navn</a> som "navn"-noden,
ikke en heading. Heuristikken ser ikke disse, så vi parser eksplisitt.

Markup-mønster:
  <div class="sc-hn5swi-0 ...">
    <a class="... name" href="/megler/...">Navn</a>
    <span class="title">Rolle</span>
    <span class="contact-info">
      <span class="phone"><a href="tel:+4791234567">...</a></span>
    </span>
  </div>

Ingen e-post i listen — kun lenke til /megler/<slug>/kontakt.
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

    # Finn alle ansatt-navn-anchor'er. To strategier:
    #   1) <a class*="name" href="/megler/<slug>"> (primær)
    #   2) Fallback: <a href="/megler/<slug>"> der teksten ser ut som et navn
    navn_anchors = []

    for a in soup.find_all("a", href=re.compile(r"^/megler/[^/]+/?$")):
        klasser = a.get("class") or []
        if any("name" in (c or "").lower() for c in klasser):
            navn_anchors.append(a)

    if not navn_anchors:
        # fallback — ta alle /megler/<slug>-lenker, men bare de som har tekst som
        # ser ut som et navn (utelukker /megler/<slug>/kontakt og «Om megler»-
        # knappene)
        for a in soup.find_all("a", href=re.compile(r"^/megler/[^/]+/?$")):
            tekst = a.get_text(strip=True)
            if tekst and " " in tekst and tekst.lower() not in {"om megler", "se profil"}:
                if re.match(r"^[A-ZÆØÅ]", tekst):
                    navn_anchors.append(a)

    ansatte = []
    seen = set()

    for a in navn_anchors:
        navn = a.get_text(strip=True)
        if not navn:
            continue

        # Felles forelder for navn + tittel + telefon
        kort = a.parent
        for _ in range(4):
            if kort is None or kort.name in (None, "html", "body"):
                break
            if kort.find("a", href=re.compile(r"^tel:")):
                break
            kort = kort.parent

        rolle = ""
        if kort is not None:
            tittel_el = kort.find(class_=re.compile(r"\btitle\b"))
            if tittel_el:
                rolle = tittel_el.get_text(" ", strip=True)

        telefon = ""
        telefon_norm = ""
        if kort is not None:
            tel_el = kort.find("a", href=re.compile(r"^tel:"))
            if tel_el:
                raa = tel_el.get("href", "").replace("tel:", "")
                telefon = formater_telefon(raa)
                telefon_norm = normaliser_telefon(raa)

        fornavn, etternavn = splitt_navn(navn)
        nokkel = (navn.lower(), telefon_norm)
        if nokkel in seen:
            continue
        seen.add(nokkel)

        ansatte.append({
            "kjede": "PrivatMegleren",
            "kontor": kontor_navn,
            "kontor_url": kontor_url,
            "fornavn": fornavn,
            "etternavn": etternavn,
            "fullt_navn": navn,
            "rolle": rolle,
            "telefon": telefon,
            "telefon_normalisert": telefon_norm,
            "epost": "",
        })

    return ansatte


def pre_load(page, url):
    return
