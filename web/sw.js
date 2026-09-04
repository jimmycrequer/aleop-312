/* Les horaires sont figés jusqu'au prochain fascicule : on sert tout depuis le
   cache et on ne va sur le réseau que si la ressource manque. C'est ce qui rend
   la page utilisable à l'arrêt de bus, là où le réseau est mauvais.

   VERSION est réécrit par scripts/build.py à partir du contenu publié : un
   nouveau fascicule change la version, ce qui purge l'ancien cache. */
const VERSION = "dev";

const SHELL = "shell-" + VERSION;
const FONTS = "fonts-v1";

/* app.css, app.js et data.js n'existent que dans web/ : dans docs/ ils sont
   déjà dans le HTML. On met donc chaque entrée en cache séparément, sans faire
   échouer l'installation si l'une manque. */
const SHELL_FILES = [
  "./",
  "./index.html",
  "./app.css",
  "./app.js",
  "./data.js",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png",
];

const isFont = (url) =>
  url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL).then((cache) =>
      Promise.allSettled(SHELL_FILES.map((f) => cache.add(new Request(f, { cache: "reload" }))))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== SHELL && k !== FONTS).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin && !isFont(url)) return;

  event.respondWith(
    caches.match(request).then((hit) => {
      if (hit) return hit;

      return fetch(request).then((response) => {
        /* Les fichiers de police sont servis en opaque (cross-origin) : on les
           garde tels quels, c'est suffisant pour les réafficher hors ligne. */
        if (response.ok || response.type === "opaque") {
          const copy = response.clone();
          caches.open(isFont(url) ? FONTS : SHELL).then((cache) => cache.put(request, copy));
        }
        return response;
      }).catch(() => {
        /* Hors ligne sur une URL jamais visitée : on rend quand même la page. */
        if (request.mode === "navigate") return caches.match("./index.html");
        return Response.error();
      });
    })
  );
});
