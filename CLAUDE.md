# CLAUDE.md

Notes pour Claude Code (et pour un humain de passage). Le dépôt, ses commentaires
et ses messages de commit sont en français : écrire en français.

## Le projet en une phrase

Page statique qui répond à « à quelle heure passe le car 312 tel jour ? » entre
**Moulin de la Chaussée** (Saint-Philbert-de-Grand-Lieu) et **Pirmil** (Nantes), dans les deux sens,
à partir du fascicule PDF Aléop. Pas de serveur, pas de framework, pas de dépendance
au runtime.

## Commandes

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

.venv/bin/python scripts/parse_pdf.py    # data/*.pdf  -> web/data.js
.venv/bin/python scripts/make_icons.py   # -> web/icon-192.png, web/icon-512.png
python3 scripts/build.py                  # web/ -> docs/  (aucune dépendance)
```

Pour vérifier une modification : ouvrir `web/index.html` en double-clic suffit
pour l'affichage ; pour tester le service worker il faut du http, donc
`python3 -m http.server -d docs` puis <http://localhost:8000>.

Pas de tests, pas de linter, pas de CI : la vérification est visuelle.

## Chaîne de production

```
data/*.pdf ──parse_pdf.py──> web/data.js ─┐
web/{index.html,app.css,app.js,sw.js} ────┼──build.py──> docs/
web/{manifest.webmanifest,icon-*.png} ────┘
```

- **`web/` est la source, `docs/` est généré.** Ne jamais éditer `docs/` à la main :
  la prochaine exécution de `build.py` l'écrase. GitHub Pages sert `main` / `/docs`.
- `build.py` produit une page **autonome** : il inline `app.css`, `data.js` et `app.js`
  dans `index.html`. Il s'appuie sur des balises littérales et échoue (assert) si on
  les modifie — garder telles quelles `<link rel="stylesheet" href="app.css">`,
  `<script src="data.js"></script>`, `<script src="app.js"></script>`, ainsi que
  `<title>`, `</head>` et `<body>`/`</body>` (découpe de `artifact.html`).
- `sw.js` doit garder la ligne `const VERSION = "dev";` telle quelle : `build.py` la
  réécrit avec un hash du contenu publié, ce qui purge l'ancien cache quand les
  horaires changent.
- `web/data.js` est versionné : la page se construit sans le PDF. Le fascicule, lui,
  n'est pas redistribué (voir `.gitignore`) et se récupère sur aleop.paysdelaloire.fr.

## Nouveau fascicule : ce qu'il faut reprendre à la main

`parse_pdf.py` reconstruit la grille à partir des positions (x, y) du texte et des
rectangles vectoriels de l'en-tête — le PDF n'a aucune structure tabulaire. Après
chaque nouveau fascicule :

1. mettre à jour la constante `PDF` (le nom de fichier porte les dates) ;
2. relire dans `main()` : `validity`, `vacances`, `feries`, `sansService`. Ces
   valeurs sont recopiées du calendrier imprimé sur le fascicule (zone B), le
   parser ne les déduit pas ;
3. relancer `parse_pdf.py` puis `build.py`, et vérifier quelques courses à l'écran
   contre le PDF.

## Modèle de données (`window.SCHEDULES`)

Une _course_ = `{dir: "nantes"|"philbert", dep, arr, days, scolaire, vacances}`.
`days` utilise 1 = lundi … 7 = dimanche. Les règles imprimées sur le fascicule sont
appliquées côté client dans `resolve()` / `tripsFor()` (`web/app.js`) : un jour férié
circule **comme un dimanche** (jour forcé à 7), une date en vacances scolaires bascule
sur la colonne `vacances` au lieu de `scolaire`, `sansService` et hors période de
validité rendent une liste vide.

## Conventions

- `web/app.js` : un IIFE en JS ancien style (`var`, `function`), sans build ni
  framework, DOM construit à la main via le helper `el()`. Rester dans ce style.
- CSS : variables sur `:root`, thème clair/sombre via `prefers-color-scheme` **et**
  `[data-theme]`. Palette relevée sur le fascicule lui-même (outremer `#000FA0`).
- Les commentaires expliquent le _pourquoi_ (une contrainte du PDF, du service worker,
  du hors-ligne), pas le _quoi_. Peu nombreux, en français, sans accents dans les
  fichiers Python (les chaînes affichées, elles, sont accentuées).
- Commits en français, style Conventional Commits (`feat:`, `refactor:`, `chore:`).
