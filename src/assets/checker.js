// M2M destination checker: transparent, rule-based scoring that runs in the browser.
// Data (country rules + interface text) is embedded in the page by src/build.py.
(function () {
  "use strict";
  var dataEl = document.getElementById("checker-data");
  var form = document.getElementById("checker");
  if (!dataEl || !form) return;
  var D = JSON.parse(dataEl.textContent);
  var T = D.text;

  function fmt(s, vars) {
    return s.replace(/\{(\w+)\}/g, function (_, k) { return vars[k] != null ? vars[k] : ""; });
  }
  function band(n) { return n ? n.toFixed(1) : ""; }

  // Score one country for a profile. Returns null when the country is not a realistic option.
  function score(c, p) {
    var r = c.rules, s = 0, pros = [], cons = [];
    if (p.level === "mbbs" && !r.mbbs) return null;
    if (p.level === "phd" && !r.phd) return null;

    // Budget: cost tier against the chosen band
    var over = r.cost - p.budget;
    if (over <= 0) { s += over <= -2 ? 2 : 3; pros.push(T.reasons.budget_ok); }
    else if (over === 1 && (r.sch >= 1 || p.marks >= 75)) { cons.push(T.reasons.budget_sch); }
    else return null;

    // English
    if (p.english === 0) {
      if (r.ielts === 0) { s += 1; pros.push(T.reasons.eng_free); }
      else if (r.no_test && p.emi) { s += 1; pros.push(T.reasons.eng_none_ok); }
      else { s -= 1; cons.push(fmt(T.reasons.eng_none, { req: band(r.ielts) })); }
    } else if (r.ielts === 0 || p.english >= r.ielts) {
      s += 2; pros.push(fmt(T.reasons.eng_ok, { req: band(r.ielts) || "-" }));
    } else if (p.english >= r.ielts - 0.5) {
      cons.push(fmt(T.reasons.eng_low, { req: band(r.ielts) }));
    } else {
      s -= 2; cons.push(fmt(T.reasons.eng_low, { req: band(r.ielts) }));
    }

    // Academic record and scholarships
    if (p.marks >= 75 && r.sch >= 1) { s += r.sch; pros.push(T.reasons.marks_sch); }
    if ((p.marks < 60 && r.compete === 3) || (p.marks < 55 && r.compete === 2)) {
      s -= 2; cons.push(T.reasons.marks_low);
    }

    // Study gap
    if (p.gap > r.gap) { s -= 2; cons.push(T.reasons.gap_warn); }

    if (p.level === "phd") { s += 1; pros.push(T.reasons.phd); }
    if (p.level === "mbbs") { pros.push(T.reasons.mbbs); }
    if (c.slug === "canada") { cons.push(T.reasons.canada); }
    s += r.pop || 0;

    var label = s >= 5 ? "strong" : s >= 3 ? "good" : "possible";
    return { c: c, s: s, pros: pros, cons: cons, label: label };
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function optText(id) {
    var s = document.getElementById(id);
    return s.options[s.selectedIndex].text;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var marksInput = document.getElementById("k-marks");
    var marks = Number(marksInput.value);
    if (!marksInput.value || isNaN(marks) || marks < 30 || marks > 100) {
      marksInput.setCustomValidity(T.marks_invalid);
      marksInput.reportValidity();
      return;
    }
    var p = {
      level: document.getElementById("k-level").value,
      marks: marks,
      english: Number(document.getElementById("k-english").value),
      emi: document.getElementById("k-emi").checked,
      budget: Number(document.getElementById("k-budget").value),
      gap: Number(document.getElementById("k-gap").value)
    };
    var res = D.countries.map(function (c) { return score(c, p); })
      .filter(Boolean)
      .sort(function (a, b) {
        return b.s - a.s || Math.abs(p.budget - a.c.rules.cost) - Math.abs(p.budget - b.c.rules.cost);
      })
      .slice(0, 6);

    var out = document.getElementById("results");
    out.innerHTML = "";
    out.hidden = false;
    out.appendChild(el("h2", null, T.results));
    if (!res.length) {
      out.appendChild(el("p", "none", T.none));
    }
    var list = el("ol", "r-list");
    res.forEach(function (r) {
      var li = el("li", "r-card r-" + r.label);
      var head = el("div", "r-head");
      var code = el("span", "iata", r.c.code); code.dir = "ltr";
      head.appendChild(code);
      head.appendChild(el("h3", null, r.c.name));
      head.appendChild(el("span", "r-label", T.labels[r.label]));
      li.appendChild(head);
      var ul = el("ul", "r-reasons");
      r.pros.forEach(function (t) { ul.appendChild(el("li", "pro", t)); });
      r.cons.forEach(function (t) { ul.appendChild(el("li", "con", t)); });
      li.appendChild(ul);
      var a = el("a", "r-link", fmt(T.view, { name: r.c.name }));
      a.href = r.c.url;
      li.appendChild(a);
      list.appendChild(li);
    });
    out.appendChild(list);

    var L = T.summary_labels;
    var msg = [T.wa_intro,
      L.level + ": " + optText("k-level"),
      L.marks + ": " + marks + "%",
      L.english + ": " + optText("k-english") + (p.emi ? " (EMI)" : ""),
      L.budget + ": " + optText("k-budget"),
      L.gap + ": " + optText("k-gap"),
      L.results + ": " + res.map(function (r) { return r.c.name; }).join(", ")].join("\n");
    var wa = el("a", "btn btn-gold", T.wa);
    wa.href = "https://wa.me/" + D.wa + "?text=" + encodeURIComponent(msg);
    wa.target = "_blank"; wa.rel = "noopener";
    out.appendChild(wa);
    out.appendChild(el("p", "disclaimer", T.disclaimer));
    out.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  document.getElementById("k-marks").addEventListener("input", function () { this.setCustomValidity(""); });
})();
