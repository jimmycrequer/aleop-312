#!/usr/bin/env python3
"""Assemble la page a deployer.

docs/index.html contient les horaires en dur : il s'ouvre en file:// comme il se
depose sur un hebergeur statique. docs/artifact.html est la meme page sans
l'ossature <html>/<head>/<body>, pour un hote qui la fournit deja.
"""
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
SITE = ROOT / "docs"
ASSETS = ["manifest.webmanifest", "icon-192.png", "icon-512.png"]

def read(name):
    return (WEB / name).read_text(encoding="utf-8")


# La page servie reste un fichier unique : c'est ce qui la rend consultable
# hors ligne et ouvrable en double-clic, sans rien a cote.
standalone = read("index.html")
for tag, inline, source in [
    ('<link rel="stylesheet" href="app.css">', "style", "app.css"),
    ('<script src="data.js"></script>', "script", "data.js"),
    ('<script src="app.js"></script>', "script", "app.js"),
]:
    assert tag in standalone, f"balise introuvable dans index.html : {tag}"
    standalone = standalone.replace(
        tag, f"<{inline}>\n{read(source)}</{inline}>")

SITE.mkdir(exist_ok=True)
# GitHub Pages passe le dossier dans Jekyll sans ce fichier.
(SITE / ".nojekyll").touch()
(SITE / "index.html").write_text(standalone, encoding="utf-8")
for name in ASSETS:
    shutil.copy2(WEB / name, SITE / name)

# La version du cache suit le contenu publie : un nouveau fascicule purge
# l'ancien cache au lieu de laisser d'anciens horaires en place.
version = hashlib.sha256(standalone.encode("utf-8")).hexdigest()[:12]
sw = (WEB / "sw.js").read_text(encoding="utf-8").replace('const VERSION = "dev";',
                                                         f'const VERSION = "{version}";')
(SITE / "sw.js").write_text(sw, encoding="utf-8")

# Variante hebergee : ni manifeste ni icone a cote de la page.
artifact = standalone[standalone.index("<title>"):standalone.index("</head>")]
artifact = "\n".join(l for l in artifact.splitlines()
                     if "manifest.webmanifest" not in l and "apple-touch-icon" not in l)
artifact += standalone[standalone.index("<body>") + len("<body>"):standalone.index("</body>")]
(SITE / "artifact.html").write_text(artifact, encoding="utf-8")

print(f"docs/ : index.html, sw.js ({version}), artifact.html, " + ", ".join(ASSETS))
