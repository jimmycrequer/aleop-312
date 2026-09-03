#!/usr/bin/env python3
"""Genere les icones d'installation : le numero de ligne sur l'outremer du fascicule.

Le chiffre reste dans la zone sure centrale (80 %) pour que la meme image serve
aussi d'icone maskable sur Android.
"""
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
OUTREMER = (0, 15 / 255, 160 / 255)
CAP_HEIGHT = 0.717  # Helvetica, pour centrer optiquement les capitales

for size in (192, 512):
    doc = pymupdf.open()
    page = doc.new_page(width=size, height=size)
    page.draw_rect(page.rect, color=None, fill=OUTREMER)

    fs = size * 0.36
    width = pymupdf.get_text_length("312", fontname="hebo", fontsize=fs)
    page.insert_text(((size - width) / 2, size / 2 + fs * CAP_HEIGHT / 2),
                     "312", fontname="hebo", fontsize=fs, color=(1, 1, 1))

    page.get_pixmap(dpi=72).save(WEB / f"icon-{size}.png")
    print(f"web/icon-{size}.png")
