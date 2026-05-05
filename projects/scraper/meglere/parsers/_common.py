"""
Felles heuristikk-parser for megler-ansattlister.

Strategi: finn alle <a href="tel:..."> og <a href="mailto:...">,
gå opp DOM-treet til en "kort"-rot som også inneholder et navn
(h1-h6 eller strong/b), og hent ut navn + rolle + telefon + e-post.

Robust mot små markup-endringer mellom kjeder.
"""

import re
from bs4 import BeautifulSoup, Tag


_NAME_BLACKLIST = {
    "kontakt", "kontakt oss", "ring oss", "send e-post", "om oss",
    "vurdering", "salgsoppgave", "boligsøk", "boligsok", "tjenester",
    "kontoret", "ansatte", "meglere", "megler", "team",
    "personvern", "om bedriften",
}


def _digits_only(s):
    return re.sub(r"\D", "", s or "")


def formater_telefon(raa):
    """Match formater_telefon i scripts_brev/scrape_postcode_1881.py — produserer
    'XXX XX XXX' for 8-sifret norsk nummer, ellers de rene sifrene."""
    tall = _digits_only(raa)
    if tall.startswith("0047"):
        tall = tall[4:]
    elif tall.startswith("47") and len(tall) == 10:
        tall = tall[2:]
    if len(tall) == 8:
        return f"{tall[:3]} {tall[3:5]} {tall[5:]}"
    return tall


def normaliser_telefon(raa):
    """Kun siffer, uten landkode +47 — for matching-nøkkel."""
    tall = _digits_only(raa)
    if tall.startswith("0047"):
        tall = tall[4:]
    elif tall.startswith("47") and len(tall) == 10:
        tall = tall[2:]
    return tall


def splitt_navn(fullt_navn):
    deler = fullt_navn.strip().split()
    if len(deler) >= 2:
        return " ".join(deler[:-1]), deler[-1]
    return fullt_navn.strip(), ""


def _ser_ut_som_navn(s):
    if not s or len(s) < 3 or len(s) > 80:
        return False
    s_low = s.lower().strip()
    if s_low in _NAME_BLACKLIST:
        return False
    if any(b in s_low for b in ("kontakt oss", "om oss", "send e-post", "ring oss")):
        return False
    if re.search(r"\d", s):
        return False
    ord_liste = s.split()
    if len(ord_liste) < 2 or len(ord_liste) > 5:
        return False
    if not all(re.match(r"^[A-ZÆØÅ]", o) for o in ord_liste if o):
        return False
    return True


def _finn_navn_i_kort(kort):
    for tag in ("h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"):
        for el in kort.find_all(tag):
            tekst = el.get_text(" ", strip=True)
            if _ser_ut_som_navn(tekst):
                return tekst
    for el in kort.find_all(True):
        if el.name in ("a", "script", "style"):
            continue
        tekst = el.get_text(" ", strip=True)
        if _ser_ut_som_navn(tekst):
            return tekst
    return None


def _finn_rolle_i_kort(kort, navn):
    """Tekst i kortet som ikke er navn/telefon/e-post. Korteste ikke-tomme linje
    som inneholder et bokstav-tegn og ikke ser ut som et navn."""
    kandidater = []
    for el in kort.find_all(["p", "span", "div", "small", "em", "li"]):
        tekst = el.get_text(" ", strip=True)
        if not tekst or tekst == navn:
            continue
        if "@" in tekst or re.search(r"\+?\d[\d\s]{5,}", tekst):
            continue
        if not re.search(r"[A-Za-zÆØÅæøå]", tekst):
            continue
        if 2 <= len(tekst) <= 120 and tekst != navn and navn not in tekst:
            kandidater.append(tekst)
    if not kandidater:
        return ""
    kandidater.sort(key=lambda s: (len(s), s))
    for k in kandidater:
        if not _ser_ut_som_navn(k):
            return k
    return kandidater[0]


def _finn_kort_for_anchor(anchor, max_steg=8):
    """Gå opp fra anchor til en stamfar som også inneholder et navn-tag."""
    node = anchor
    for _ in range(max_steg):
        if node is None or node.name in (None, "[document]", "html", "body"):
            break
        for tag in ("h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"):
            if node.find(tag):
                tekst = node.find(tag).get_text(" ", strip=True)
                if _ser_ut_som_navn(tekst):
                    return node
        node = node.parent
    return None


def _id_for_node(node):
    """Stabil id basert på node-objektets identitet."""
    return id(node)


def extract_persons_heuristic(html, kjede, kontor_navn, kontor_url):
    """Returnerer liste av ansatt-records ekstrahert fra HTML."""
    soup = BeautifulSoup(html, "lxml")

    tel_anchors = soup.select('a[href^="tel:"]')
    mail_anchors = soup.select('a[href^="mailto:"]')

    kort_til_anchors = {}

    for a in tel_anchors + mail_anchors:
        kort = _finn_kort_for_anchor(a)
        if kort is None:
            continue
        slot = kort_til_anchors.setdefault(_id_for_node(kort), {"node": kort, "tel": None, "mail": None})
        if a.get("href", "").startswith("tel:") and slot["tel"] is None:
            slot["tel"] = a
        elif a.get("href", "").startswith("mailto:") and slot["mail"] is None:
            slot["mail"] = a

    ansatte = []
    seen = set()

    for slot in kort_til_anchors.values():
        kort = slot["node"]
        navn = _finn_navn_i_kort(kort)
        if not navn:
            continue

        tel_href = slot["tel"].get("href", "") if slot["tel"] else ""
        mail_href = slot["mail"].get("href", "") if slot["mail"] else ""

        telefon = formater_telefon(tel_href.replace("tel:", "")) if tel_href else ""
        telefon_norm = normaliser_telefon(tel_href.replace("tel:", "")) if tel_href else ""
        epost = mail_href.replace("mailto:", "").split("?")[0].strip() if mail_href else ""

        rolle = _finn_rolle_i_kort(kort, navn)
        fornavn, etternavn = splitt_navn(navn)

        nokkel = (navn.lower(), telefon_norm, epost.lower())
        if nokkel in seen:
            continue
        seen.add(nokkel)

        ansatte.append({
            "kjede": kjede,
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
