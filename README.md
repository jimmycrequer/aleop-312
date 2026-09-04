## Objectif

Consulter en un coup d'œil les horaires du car Aléop 312 entre Saint-Philbert-de-Grand-Lieu
et Nantes, sans rouvrir le fascicule.

Le PDF officiel a la bonne information mais la rend pénible à lire au quotidien : il déroule
tous les arrêts de la ligne alors que deux m'intéressent, et il faut croiser soi-même les
colonnes — semaine, mercredi, week-end, période scolaire ou vacances — pour savoir laquelle
s'applique à la date qu'on a en tête.

Ici on choisit une date, et la page affiche les seules courses qui relient mes deux arrêts ce
jour-là, dans les deux sens, la question des jours fériés et des vacances scolaires étant déjà
tranchée.

La ligne et les arrêts sont volontairement en dur : c'est un utilitaire personnel, pas un
moteur de recherche d'itinéraires.

## Utilisation

`web/index.html` affiche, pour une date donnée, les courses qui desservent **Moulin de la Chaussée**
(Saint-Philbert-de-Grand-Lieu) et **Pirmil** (Nantes), dans les deux sens. Les jours fériés et les vacances scolaires
sont résolus automatiquement à partir du calendrier imprimé sur le fascicule.

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/parse_pdf.py    # PDF -> web/data.js
.venv/bin/python scripts/make_icons.py   # icônes d'installation
python3 scripts/build.py                 # -> docs/ (page autonome + service worker)
```

`docs/` se dépose tel quel sur n'importe quel hébergeur statique, et c'est le dossier que
GitHub Pages sert (Settings → Pages → _Deploy from a branch_ → `main` / `/docs`). En HTTPS, le service
worker met la page et les polices en cache : une fois ajoutée à l'écran d'accueil, elle
s'ouvre hors ligne. La version du cache suit le contenu publié, donc un nouveau fascicule
remplace les anciens horaires au lieu de les laisser en place.

Le fascicule PDF n'est pas versionné : récupérez-le sur [aleop.paysdelaloire.fr](https://aleop.paysdelaloire.fr)
et déposez-le dans `data/` avant de relancer le parser. `web/data.js`, lui, est versionné, donc la page
se construit sans le PDF.

Le parser reconstruit la grille du fascicule à partir des positions du texte et des rectangles
d'en-tête ; il faut le relancer à chaque nouveau fascicule, et vérifier que la période de validité,
les vacances et les jours fériés dans `scripts/parse_pdf.py` correspondent.

## Organisation

```
data/       le fascicule PDF (non versionné)
scripts/    parse_pdf.py (PDF -> data.js), make_icons.py, build.py (web/ -> docs/)
web/        les sources : index.html, app.css, app.js, sw.js, data.js, manifeste, icônes
docs/       la page publiée, générée par build.py — ne pas éditer à la main
```

`build.py` inline le CSS, les données et le script dans `docs/index.html` pour n'avoir
qu'un seul fichier à servir, et écrit en plus `docs/artifact.html`, la même page sans
l'ossature `<html>`/`<head>`/`<body>` pour un hôte qui la fournit déjà.

Il n'y a ni framework ni étape de build côté navigateur : `web/index.html` s'ouvre
directement en double-clic. Pour tester le service worker, il faut du http :
`python3 -m http.server -d docs`.

Voir [CLAUDE.md](CLAUDE.md) pour les détails de la chaîne de production et les
conventions du code.
