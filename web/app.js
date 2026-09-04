(function () {
  "use strict";

  var D = window.SCHEDULES;
  var JOURS = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];
  var MOIS = ["janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre", "décembre"];

  var elDate = document.getElementById("date");
  var elNote = document.getElementById("note");
  var elWarn = document.getElementById("warn");
  var elDirs = document.getElementById("directions");

  function iso(d) {
    return d.getFullYear() + "-" +
      String(d.getMonth() + 1).padStart(2, "0") + "-" +
      String(d.getDate()).padStart(2, "0");
  }

  function fromIso(s) {
    var p = s.split("-");
    return new Date(+p[0], +p[1] - 1, +p[2]);
  }

  function longDate(s) {
    var d = fromIso(s);
    return JOURS[d.getDay()] + " " + (d.getDate() === 1 ? "1er" : d.getDate()) +
      " " + MOIS[d.getMonth()] + " " + d.getFullYear();
  }

  function minutes(hhmm) {
    var p = hhmm.split(":");
    return +p[0] * 60 + +p[1];
  }

  /* Applique les règles imprimées sur le fascicule : un jour férié roule comme
     un dimanche, et les périodes de vacances basculent la colonne utilisée. */
  function resolve(s) {
    var ctx = { date: s, ferie: D.feries[s] || null, conge: null };
    ctx.horsPeriode = s < D.validity.start || s > D.validity.end;
    ctx.sansService = D.sansService[s] || null;
    for (var i = 0; i < D.vacances.length; i++) {
      if (s >= D.vacances[i].debut && s <= D.vacances[i].fin) { ctx.conge = D.vacances[i]; break; }
    }
    var jour = fromIso(s).getDay();
    ctx.jour = ctx.ferie ? 7 : (jour === 0 ? 7 : jour);
    return ctx;
  }

  function tripsFor(ctx, dir) {
    if (ctx.sansService || ctx.horsPeriode) return [];
    return D.trips.filter(function (t) {
      return t.dir === dir &&
        t.days.indexOf(ctx.jour) !== -1 &&
        (ctx.conge ? t.vacances : t.scolaire);
    }).sort(function (a, b) { return minutes(a.dep) - minutes(b.dep); });
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function renderNote(ctx) {
    elNote.textContent = "";
    var jour = el("b", null, longDate(ctx.date));
    elNote.appendChild(jour);
    if (ctx.sansService) {
      elNote.appendChild(document.createTextNode(" — aucun service."));
      return;
    }
    if (ctx.ferie) {
      elNote.appendChild(document.createTextNode(" — " + ctx.ferie + ", le car circule comme un dimanche."));
    }
    if (ctx.conge) {
      elNote.appendChild(document.createTextNode(ctx.ferie ? " " : " — "));
      elNote.appendChild(el("span", "vac", ctx.conge.nom));
      elNote.appendChild(document.createTextNode(ctx.ferie ? "." : " : horaires de vacances."));
    } else if (!ctx.ferie) {
      elNote.appendChild(document.createTextNode(" — période scolaire."));
    }
  }

  function renderDirection(ctx, dir, titre, sous) {
    var box = el("section", "dir");
    var h = el("h2", null, titre);
    h.appendChild(el("small", null, sous));
    box.appendChild(h);

    var list = tripsFor(ctx, dir);
    if (!list.length) {
      box.appendChild(el("p", "empty", ctx.sansService
        ? "Aucun service le " + ctx.sansService + "."
        : ctx.horsPeriode ? "Hors période couverte par le fascicule."
        : "Aucun car dans ce sens ce jour-là."));
      return box;
    }

    var ul = el("ul", "legs");
    list.forEach(function (t) {
      var li = document.createElement("li");
      var row = el("div", "leg");
      row.appendChild(el("time", null, t.dep));
      var th = el("span", "thread");
      th.appendChild(el("span", null, (minutes(t.arr) - minutes(t.dep)) + " min"));
      row.appendChild(th);
      row.appendChild(el("time", null, t.arr));
      li.appendChild(row);
      ul.appendChild(li);
    });
    box.appendChild(ul);
    return box;
  }

  function render() {
    var s = elDate.value;
    if (!s) return;
    var ctx = resolve(s);
    renderNote(ctx);

    elWarn.textContent = ctx.horsPeriode
      ? "Ce fascicule couvre du " + longDate(D.validity.start) + " au " + longDate(D.validity.end) + "."
      : "";

    elDirs.textContent = "";
    elDirs.appendChild(renderDirection(ctx, "nantes", "Vers Nantes",
      "Moulin de la Chaussée → Pirmil"));
    elDirs.appendChild(renderDirection(ctx, "philbert", "Vers Saint-Philbert",
      "Pirmil → Moulin de la Chaussée"));
  }

  function shift(days) {
    var d = fromIso(elDate.value);
    d.setDate(d.getDate() + days);
    elDate.value = iso(d);
    render();
  }

  document.getElementById("prev").onclick = function () { shift(-1); };
  document.getElementById("next").onclick = function () { shift(1); };
  document.getElementById("today").onclick = function () {
    elDate.value = iso(new Date());
    render();
  };
  elDate.onchange = render;

  elDate.min = D.validity.start;
  elDate.max = D.validity.end;
  elDate.value = iso(new Date());

  var pied = "Ligne " + D.line + " Aléop, horaires du " + longDate(D.validity.start) +
    " au " + longDate(D.validity.end) + ". Les arrêts intermédiaires ne sont pas affichés : " +
    "seules les courses desservant les deux arrêts apparaissent.";

  /* Le service worker n'est possible qu'en http(s) : ouvert en file://, la page
     marche déjà hors ligne, il n'y a rien à installer. */
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    navigator.serviceWorker.register("sw.js").then(function () {
      document.getElementById("footer").textContent = pied +
        " Ajoutez la page à votre écran d’accueil pour la consulter hors ligne.";
    }, function () { /* pas de sw.js à côté de la page : sans conséquence */ });
  }

  document.getElementById("footer").textContent = pied;
  render();
})();
