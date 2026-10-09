/* Public business website: navbar, reveal, counters, parallax, filters */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var nav = document.getElementById("nav");
  var toggle = document.getElementById("navToggle");

  /* ---------- Navbar: scrolled state + mobile menu ---------- */
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      var y = window.scrollY || 0;
      if (nav) nav.classList.toggle("is-scrolled", y > 24);
      var bg = document.querySelector("[data-parallax]");
      if (bg && !reduceMotion && y < window.innerHeight * 1.2) {
        bg.style.transform = "translate3d(0," + (y * parseFloat(bg.dataset.parallax || "0.15")).toFixed(1) + "px,0)";
      }
      ticking = false;
    });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  function setMenu(open) {
    if (!toggle || !nav) return;
    toggle.setAttribute("aria-expanded", String(open));
    nav.classList.toggle("is-open", open);
    document.body.classList.toggle("nav-open", open);
  }
  if (toggle) {
    toggle.addEventListener("click", function () {
      setMenu(toggle.getAttribute("aria-expanded") !== "true");
    });
    document.querySelectorAll("#navMenu a").forEach(function (a) {
      a.addEventListener("click", function () { setMenu(false); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { setMenu(false); toggle.focus(); }
    });
    window.addEventListener("resize", function () { if (window.innerWidth > 860) setMenu(false); });
  }

  /* ---------- Images: fade-in and graceful fallback ---------- */
  function markLoaded(img) { img.classList.add("is-loaded"); }
  function markBroken(img) { img.classList.add("is-broken"); }
  document.querySelectorAll("img[data-fade]").forEach(function (img) {
    if (img.complete) { img.naturalWidth > 0 ? markLoaded(img) : markBroken(img); return; }
    img.addEventListener("load", function () { markLoaded(img); });
    img.addEventListener("error", function () { markBroken(img); });
  });

  /* ---------- Scroll reveal ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Counters (values come from the server-rendered text) ---------- */
  var counters = document.querySelectorAll("[data-count]");
  function runCounter(el) {
    var target = parseInt(el.dataset.count, 10);
    if (isNaN(target) || target <= 0 || reduceMotion) return;
    var start = null, duration = 1200;
    el.textContent = "0";
    function step(ts) {
      if (start === null) start = ts;
      var p = Math.min((ts - start) / duration, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) window.requestAnimationFrame(step);
    }
    window.requestAnimationFrame(step);
  }
  if ("IntersectionObserver" in window && !reduceMotion) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { runCounter(e.target); cio.unobserve(e.target); }
      });
    }, { threshold: 0.6 });
    counters.forEach(function (c) { cio.observe(c); });
  }

  /* ---------- Property filters (client-side, URL-synced) ----------
     Only filters the cards the server already rendered for THIS business,
     so it cannot reveal anything from another business. */
  var form = document.getElementById("filters");
  var grid = document.getElementById("propertyGrid");
  if (form && grid) {
    var cards = Array.prototype.slice.call(grid.querySelectorAll(".pcard"));
    var countEl = document.getElementById("resultsCount");
    var emptyEl = document.getElementById("noResults");
    var fields = ["city", "area", "type", "beds", "budget"];

    function val(name) { return form.elements[name] ? form.elements[name].value : ""; }

    function apply() {
      var budgetSel = form.elements.budget;
      var opt = budgetSel && budgetSel.selectedOptions[0];
      var min = opt && opt.value ? Number(opt.dataset.min) : null;
      var max = opt && opt.value && opt.dataset.max !== "" ? Number(opt.dataset.max) : null;
      var minBeds = Number(val("beds")) || 0;
      var shown = 0;

      cards.forEach(function (c) {
        var price = Number(c.dataset.price);
        var ok =
          (!val("city") || c.dataset.city === val("city")) &&
          (!val("area") || c.dataset.area === val("area")) &&
          (!val("type") || c.dataset.type === val("type")) &&
          (!minBeds || Number(c.dataset.beds) >= minBeds) &&
          (min === null || (price >= min && (max === null || price < max)));
        c.classList.toggle("is-hidden", !ok);
        if (ok) shown++;
      });

      if (countEl) countEl.innerHTML = "Showing <strong>" + shown + "</strong> of " + cards.length + " properties";
      if (emptyEl) emptyEl.hidden = shown !== 0;

      var params = new URLSearchParams();
      fields.forEach(function (f) { if (val(f)) params.set(f, val(f)); });
      var qs = params.toString();
      history.replaceState(null, "", window.location.pathname + (qs ? "?" + qs : "") + window.location.hash);
    }

    // Restore state from the URL (only accept values that exist as options)
    var initial = new URLSearchParams(window.location.search);
    fields.forEach(function (f) {
      var el = form.elements[f], v = initial.get(f);
      if (el && v && Array.prototype.some.call(el.options, function (o) { return o.value === v; })) el.value = v;
    });

    form.addEventListener("change", apply);
    var reset = document.getElementById("filtersReset");
    if (reset) reset.addEventListener("click", function () { form.reset(); apply(); });
    apply();
    if (initial.toString() && document.getElementById("properties")) {
      // Filters came from a shared link: make sure results are visible
      cards.forEach(function (c) { c.classList.add("is-visible"); });
    }
  }
})();
