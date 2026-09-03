#!/usr/bin/env python3
"""Assemble une page autonome : les horaires sont injectes dans le HTML, ce qui
permet d'ouvrir le fichier directement (file://) ou de le deposer tel quel sur
un hebergeur statique."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DIST = ROOT / "dist"

html = (WEB / "index.html").read_text(encoding="utf-8")
data = (WEB / "data.js").read_text(encoding="utf-8")

standalone = html.replace('<script src="data.js"></script>',
                          "<script>\n" + data + "</script>")

DIST.mkdir(exist_ok=True)
(DIST / "index.html").write_text(standalone, encoding="utf-8")

# Variante sans <html>/<head>/<body> pour un hote qui fournit deja l'ossature.
head = standalone[standalone.index("<title>"):standalone.index("</head>")]
body = standalone[standalone.index("<body>") + len("<body>"):standalone.index("</body>")]
(DIST / "artifact.html").write_text(head + body, encoding="utf-8")

print("dist/index.html + dist/artifact.html")
