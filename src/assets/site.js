// M2M Global Consultants: menu, country filter and WhatsApp enquiry form.
(function () {
  "use strict";

  // Mobile menu
  var btn = document.getElementById("menuBtn");
  var nav = document.getElementById("mainNav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        nav.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
      }
    });
  }

  var yr = document.getElementById("yr");
  if (yr) yr.textContent = new Date().getFullYear();

  // Country region filter on the home page
  var chips = document.querySelectorAll(".chip");
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var f = chip.dataset.f;
      chips.forEach(function (x) {
        var on = x === chip;
        x.classList.toggle("on", on);
        x.setAttribute("aria-pressed", on ? "true" : "false");
      });
      document.querySelectorAll("#destGrid .d").forEach(function (card) {
        card.hidden = !(f === "all" || card.dataset.r === f);
      });
    });
  });

  // "Ask about this" on a service pre-selects it in the form
  document.querySelectorAll("[data-service]").forEach(function (a) {
    a.addEventListener("click", function () {
      var s = document.getElementById("f-service");
      if (s) s.selectedIndex = Number(a.dataset.service) || 0;
    });
  });

  // Enquiry form: builds a WhatsApp message (a static site has no server to receive forms)
  var form = document.getElementById("enquiry");
  if (!form) return;
  var labels = JSON.parse(form.dataset.labels || "{}");
  function val(id) {
    var el = document.getElementById(id);
    return el ? el.value.trim() : "";
  }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var name = document.getElementById("f-name");
    var phone = document.getElementById("f-phone");
    var missing = !val("f-name") ? name : !val("f-phone") ? phone : null;
    if (missing) {
      missing.setCustomValidity(form.dataset.required || "Required");
      missing.reportValidity();
      missing.focus();
      return;
    }
    var ids = ["f-name", "f-phone", "f-service", "f-country", "f-level", "f-mode", "f-msg"];
    var keys = ["f_name", "f_phone", "f_service", "f_country", "f_level", "f_mode", "f_msg"];
    var lines = [form.dataset.greeting];
    ids.forEach(function (id, i) {
      var v = val(id);
      if (v) lines.push((labels[keys[i]] || id) + ": " + v);
    });
    var link = document.getElementById("waLink");
    link.href = "https://wa.me/" + form.dataset.wa + "?text=" + encodeURIComponent(lines.join("\n"));
    document.getElementById("waOut").hidden = false;
    link.focus();
  });
  form.querySelectorAll("input").forEach(function (i) {
    i.addEventListener("input", function () { i.setCustomValidity(""); });
  });
})();
