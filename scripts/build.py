#!/usr/bin/env python3
"""Assemble la page a deployer.

dist/index.html contient les horaires en dur : il s'ouvre en file:// comme il se
depose sur un hebergeur statique. dist/artifact.html est la meme page sans
l'ossature <html>/<head>/<body>, pour un hote qui la fournit deja.
"""
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DIST = ROOT / "dist"
ASSETS = ["manifest.webmanifest", "icon-192.png", "icon-512.png"]

html = (WEB / "index.html").read_text(encoding="utf-8")
data = (WEB / "data.js").read_text(encoding="utf-8")

standalone = html.replace('<script src="data.js"></script>', "<script>\n" + data + "</script>")

DIST.mkdir(exist_ok=True)
(DIST / "index.html").write_text(standalone, encoding="utf-8")
for name in ASSETS:
    shutil.copy2(WEB / name, DIST / name)

# La version du cache suit le contenu publie : un nouveau fascicule purge
# l'ancien cache au lieu de laisser d'anciens horaires en place.
version = hashlib.sha256(standalone.encode("utf-8")).hexdigest()[:12]
sw = (WEB / "sw.js").read_text(encoding="utf-8").replace('const VERSION = "dev";',
                                                         f'const VERSION = "{version}";')
(DIST / "sw.js").write_text(sw, encoding="utf-8")

# Variante hebergee : ni manifeste ni icone a cote de la page.
artifact = standalone[standalone.index("<title>"):standalone.index("</head>")]
artifact = "\n".join(l for l in artifact.splitlines()
                     if "manifest.webmanifest" not in l and "apple-touch-icon" not in l)
artifact += standalone[standalone.index("<body>") + len("<body>"):standalone.index("</body>")]
(DIST / "artifact.html").write_text(artifact, encoding="utf-8")

print(f"dist/ : index.html, sw.js ({version}), artifact.html, " + ", ".join(ASSETS))
