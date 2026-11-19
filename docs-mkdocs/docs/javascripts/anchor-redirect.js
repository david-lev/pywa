/* Old Sphinx anchors (#pywa.types.Message.is_reply, #v6-2-examples, …) -> the ids MkDocs generated. */
(function () {
  function resolve() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id || document.getElementById(id) || !window.PWA_ANCHOR_ALIASES) return;
    var A = window.PWA_ANCHOR_ALIASES, path = location.pathname.replace(/index\.html$/, "");
    // the site may be served under a prefix (e.g. /en/latest/): pick the longest page key the path ends with
    var key = Object.keys(A.pages)
      .filter(function (k) { return path.endsWith(k); })
      .sort(function (a, b) { return b.length - a.length; })[0];
    var target = A.global[id] || (key && A.pages[key][id]);
    var el = target && document.getElementById(target);
    if (el) { history.replaceState(null, "", "#" + target); el.scrollIntoView(); }
  }
  window.addEventListener("hashchange", resolve);
  if (typeof document$ !== "undefined") document$.subscribe(resolve); else window.addEventListener("DOMContentLoaded", resolve);
})();
