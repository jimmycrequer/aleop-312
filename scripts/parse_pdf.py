#!/usr/bin/env python3
"""Extrait les horaires de la ligne 312 (arrets Moulin de la Chaussee <-> Pirmil)
depuis le fascicule PDF Aleop, et genere web/data.js.

Le PDF n'a pas de structure tabulaire logique : on reconstruit la grille a partir
des positions (x, y) du texte et des rectangles vectoriels du bandeau d'en-tete.
"""
import json
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data" / "Horaires_Aleop_312_du_31-8-2026_au_2-7-2027.pdf"
OUT = ROOT / "web" / "data.js"

STOP_A = "Moulin de la Chaussée"   # Saint-Philbert / La Chevroliere
STOP_B = "Pirmil"                  # Nantes (Reze)

DAY_TOKENS = {
    "lun": 1, "mar": 2, "mer": 3, "jeu": 4, "ven": 5, "sam": 6, "dim": 7,
}
ORDER = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]


def parse_band_label(label):
    """'Lun à Ven' -> [1..5] ; 'Lun Mar Jeu Ven' -> [1,2,4,5] ; 'Dim & JF' -> [7]."""
    low = label.lower()
    m = re.search(r"(lun|mar|mer|jeu|ven|sam|dim)\s*à\s*(lun|mar|mer|jeu|ven|sam|dim)", low)
    if m:
        a, b = ORDER.index(m.group(1)), ORDER.index(m.group(2))
        return [DAY_TOKENS[d] for d in ORDER[a:b + 1]]
    days = [DAY_TOKENS[t] for t in re.findall(r"lun|mar|mer|jeu|ven|sam|dim", low)]
    if not days:
        raise ValueError(f"libellé de jours non reconnu : {label!r}")
    return sorted(set(days))


def words_in(page, rect):
    """Mots du PDF dont le centre tombe dans rect, tries lecture naturelle."""
    out = []
    for x0, y0, x1, y1, w, *_ in page.get_text("words"):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if rect.x0 <= cx <= rect.x1 and rect.y0 <= cy <= rect.y1:
            out.append((round(cy, 1), cx, w))
    out.sort()
    return " ".join(w for _, _, w in out)


def row_at(page, y, tol=2.0):
    """Tous les mots dont le centre vertical est a +/- tol de y."""
    out = []
    for x0, y0, x1, y1, w, *_ in page.get_text("words"):
        cy = (y0 + y1) / 2
        if abs(cy - y) <= tol:
            out.append(((x0 + x1) / 2, w))
    out.sort()
    return out


def header_rects(page, keep):
    """Rectangles remplis retenus par `keep`, dedupliques, tries par x."""
    seen, rects = set(), []
    for d in page.get_drawings():
        r = d["rect"]
        if d["type"] != "f" or r.width < 3 or r.height < 3:
            continue
        if not keep(r):
            continue
        key = (round(r.x0, 1), round(r.x1, 1))
        if key in seen:
            continue
        seen.add(key)
        rects.append(r)
    rects.sort(key=lambda r: r.x0)
    return rects


def parse_page(page):
    hit = page.search_for("Circule en période scolaire")
    if not hit:
        return None
    sco = hit[0]
    vac = page.search_for("Circule en vacances scolaires")[0]

    direction = words_in(page, pymupdf.Rect(0, 0, page.rect.x1, sco.y0)).split("→")[-1]
    direction = direction.split("Lundi")[0].split("Week")[0].strip()

    # --- colonnes : les cellules OUI/NON de la ligne "periode scolaire" ---
    cells = [r for r in header_rects(page, lambda r: abs(r.y0 - sco.y0) < 1) if r.x0 > sco.x1]
    if not cells:
        return None
    columns = [{"x0": r.x0, "x1": r.x1, "cx": (r.x0 + r.x1) / 2} for r in cells]

    def flags(anchor):
        vals = [w for cx, w in row_at(page, (anchor.y0 + anchor.y1) / 2) if w in ("OUI", "NON")]
        xs = [cx for cx, w in row_at(page, (anchor.y0 + anchor.y1) / 2) if w in ("OUI", "NON")]
        res = []
        for col in columns:
            match = [v for x, v in zip(xs, vals) if col["x0"] - 2 <= x <= col["x1"] + 2]
            res.append(match[0] == "OUI" if match else False)
        return res

    sco_flags, vac_flags = flags(sco), flags(vac)

    # --- bandes de jours : rectangles bleu clair juste au-dessus ---
    bands = [r for r in header_rects(page, lambda r: abs(r.y1 - sco.y0) < 2) if r.x0 > sco.x1]
    band_days = []
    for r in bands:
        label = words_in(page, pymupdf.Rect(r.x0 + 1, r.y0 - 30, r.x1 - 1, r.y1))
        band_days.append((r, parse_band_label(label), label))

    def days_for(col):
        for r, days, _ in band_days:
            if r.x0 - 1 <= col["cx"] <= r.x1 + 1:
                return days
        raise ValueError(f"aucune bande de jours pour la colonne x={col['cx']:.0f}")

    # --- horaires aux deux arrets ---
    def times_for(stop):
        found = page.search_for(stop)
        if not found:
            return None
        y = (found[0].y0 + found[0].y1) / 2
        res = []
        for col in columns:
            hit = [w for cx, w in row_at(page, y)
                   if col["x0"] - 3 <= cx <= col["x1"] + 3 and re.fullmatch(r"\d{1,2}:\d{2}", w)]
            res.append(hit[0].rjust(5, "0") if hit else None)
        return res

    ta, tb = times_for(STOP_A), times_for(STOP_B)
    if ta is None or tb is None:
        return None

    to_nantes = "nantes" in direction.lower()
    trips = []
    for i, col in enumerate(columns):
        dep, arr = (ta[i], tb[i]) if to_nantes else (tb[i], ta[i])
        if not dep or not arr:
            continue
        trips.append({
            "dir": "nantes" if to_nantes else "philbert",
            "dep": dep,
            "arr": arr,
            "days": days_for(col),
            "scolaire": sco_flags[i],
            "vacances": vac_flags[i],
        })
    return trips


def main():
    doc = pymupdf.open(PDF)
    trips = []
    for page in doc:
        got = parse_page(page)
        if got:
            trips.extend(got)

    # dedoublonnage : une meme course apparait parfois sur deux colonnes
    # (une par periode) -> on fusionne sur (sens, depart, arrivee, jours).
    merged = {}
    for t in trips:
        key = (t["dir"], t["dep"], t["arr"], tuple(t["days"]))
        if key in merged:
            merged[key]["scolaire"] |= t["scolaire"]
            merged[key]["vacances"] |= t["vacances"]
        else:
            merged[key] = t
    trips = sorted(merged.values(), key=lambda t: (t["dir"], t["dep"]))

    data = {
        "line": "312",
        "from": STOP_A,
        "to": STOP_B,
        "validity": {"start": "2026-08-31", "end": "2027-07-02"},
        # Calendrier imprime sur le fascicule (zone B).
        "vacances": [
            {"debut": "2026-10-17", "fin": "2026-11-01", "nom": "vacances de la Toussaint"},
            {"debut": "2026-12-19", "fin": "2027-01-03", "nom": "vacances de Noël"},
            {"debut": "2027-02-20", "fin": "2027-03-07", "nom": "vacances d'hiver"},
            {"debut": "2027-04-17", "fin": "2027-05-02", "nom": "vacances de printemps"},
            {"debut": "2027-05-06", "fin": "2027-05-09", "nom": "pont de l'Ascension"},
        ],
        "feries": {
            "2026-11-01": "Toussaint",
            "2026-11-11": "Armistice",
            "2026-12-25": "Noël",
            "2027-01-01": "Jour de l'an",
            "2027-03-29": "lundi de Pâques",
            "2027-05-06": "Ascension",
            "2027-05-08": "Victoire 1945",
            "2027-05-17": "lundi de Pentecôte",
        },
        "sansService": {"2027-05-01": "1er mai"},
        "trips": trips,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("window.SCHEDULES = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n",
                   encoding="utf-8")
    print(f"{len(trips)} courses -> {OUT.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
