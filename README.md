## Objectif

J'aimerais créer un petit utilitaire pour consulter les horaires Aléop du car 312, entre Saint Philbert de Grand Lieu et Nantes.
Pour l'instant je consulte manuellement le fasicule mais c'est fastidieux car

- il y a tous les arrêts alors que seulement 2 m'intéressent
- c'est compliqué de faire le tri entre les jours en semaine et les week-ends, les mercredi, les périodes scolaires ou vacances

Idéalement je voudrais qu'on puisse sélectionner une date et voir tous les horaires correspondants, mais seulement entre les deux arrêts qui m'intéressent.

La ligne de bus, les arrêts peuvent être hard-coded pour l'instant.

## Utilisation

`web/index.html` affiche, pour une date donnée, les courses qui desservent **Moulin de la Chaussée**
(La Chevrolière) et **Pirmil** (Rezé), dans les deux sens. Les jours fériés et les vacances scolaires
sont résolus automatiquement à partir du calendrier imprimé sur le fascicule.

```sh
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/parse_pdf.py   # PDF -> web/data.js
python scripts/build.py                 # -> dist/index.html (page autonome)
```

Le parser reconstruit la grille du fascicule à partir des positions du texte et des rectangles
d'en-tête ; il faut le relancer à chaque nouveau fascicule, et vérifier que la période de validité,
les vacances et les jours fériés en tête de `scripts/parse_pdf.py` correspondent.
