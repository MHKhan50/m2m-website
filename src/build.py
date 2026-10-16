#!/usr/bin/env python3
"""Static site generator for the M2M Global Consultants website.

Reads   src/data/countries.json  (one record per study destination, English + Urdu)
        src/data/ui.json         (all interface text, English + Urdu)
Writes  the finished website into the repository root, ready for GitHub Pages:
        index.html, ur/index.html, study-in/<slug>/index.html, ur/study-in/<slug>/index.html,
        404.html, sitemap.xml, robots.txt and assets/.

Usage:  python3 src/build.py
No third-party packages are needed.
"""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SITE = "https://m2mglobalconsultants.com"  # canonical address once the domain points here
WA = "923095685686"
PHONE_PK = ("+92 309 5685686", "+923095685686")
PHONE_UK = ("+44 7828 585686", "+447828585686")
EMAIL = "info@m2mglobalconsultants.com"
GENERATED = ["study-in", "ur", "assets", "eligibility", "services", "countries", "contact"]  # folders this script owns and rebuilds

SOCIAL = [
    ("Facebook", "fb", "https://www.facebook.com/m2mglobalconsultants/"),
    ("Instagram", "ig", "https://www.instagram.com/m2mglobalconsultants/"),
    ("X", "x", "https://x.com/M2MGConsultants"),
    ("Threads", "th", "https://www.threads.com/@m2mglobalconsultants"),
    ("LinkedIn", "in", "https://www.linkedin.com/company/108778027/"),
]
BOARD = [  # departure board on the home page: (code, city, route key)
    ("LHR", {"en": "London, UK", "ur": "لندن"}, {"en": "Student visa", "ur": "اسٹوڈنٹ ویزا"}, "open"),
    ("YYZ", {"en": "Toronto, Canada", "ur": "ٹورنٹو"}, {"en": "Admission", "ur": "داخلہ"}, "study_only"),
    ("MEL", {"en": "Melbourne, AU", "ur": "میلبورن"}, {"en": "Student visa", "ur": "اسٹوڈنٹ ویزا"}, "open"),
    ("FCO", {"en": "Rome, Italy", "ur": "روم"}, {"en": "Study · DSU", "ur": "اسٹڈی · DSU"}, "open"),
    ("BER", {"en": "Berlin, DE", "ur": "برلن"}, {"en": "Study · Schengen", "ur": "اسٹڈی · شینگن"}, "open"),
    ("VNO", {"en": "Vilnius, LT", "ur": "ولنیئس"}, {"en": "Study · Schengen", "ur": "اسٹڈی · شینگن"}, "open"),
    ("IST", {"en": "Istanbul, TR", "ur": "استنبول"}, {"en": "Study · Bursları", "ur": "اسٹڈی · Bursları"}, "open"),
]

e = html.escape


def load(name: str):
    return json.loads((SRC / "data" / name).read_text(encoding="utf-8"))


COUNTRIES = load("countries.json")
UI = load("ui.json")
ICONS = (SRC / "assets" / "icons.svg.html").read_text(encoding="utf-8")
BANNERS = load("banners.json")


def _lum(hex_colour: str) -> float:
    """Relative luminance (WCAG) of a #RRGGBB colour."""
    def ch(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def stamp_accent(flag: list[str]) -> str:
    """Pick the flag colour that reads best as line-art on the blue hero; white if none does."""
    usable = [c for c in flag if 0.08 <= _lum(c) <= 0.85]
    if not usable:
        return "#FFFFFF"
    best = max(usable, key=_lum)
    if _lum(best) < 0.25:  # lift deep reds and greens so the line-art stays readable on blue
        r, g, b = (int(best[i:i + 2], 16) for i in (1, 3, 5))
        best = "#" + "".join(f"{int(v + (255 - v) * 0.35):02X}" for v in (r, g, b))
    return best


def banner(c: dict, lang: str) -> str:
    """Decorative country banner: flag-colour bar, faded city names and a passport-style entry stamp."""
    b = BANNERS[c["slug"]]
    f = b["flag"]
    accent = stamp_accent(f)
    places = '<i aria-hidden="true">·</i>'.join(f"<span>{e(p)}</span>" for p in b["places"][lang] * 2)
    code = c["code"]
    size = 34 if len(code) <= 2 else 26 if len(code) <= 4 else 15
    city = e(b["places"]["en"][0].upper())
    stamp = f"""<svg class="stamp" viewBox="0 0 160 160" aria-hidden="true" focusable="false">
  <defs><path id="st-top" d="M 22,80 a58,58 0 1,1 116,0"/><path id="st-bot" d="M 28,80 a52,52 0 0,0 104,0"/></defs>
  <circle cx="80" cy="80" r="74" fill="none" stroke="var(--fa)" stroke-width="3"/>
  <circle cx="80" cy="80" r="64" fill="none" stroke="var(--fa)" stroke-width="1.4" stroke-dasharray="3 4"/>
  <text class="st-arc"><textPath href="#st-top" startOffset="50%" text-anchor="middle">STUDENT · ENTRY · M2M</textPath></text>
  <text class="st-code" x="80" y="80" text-anchor="middle" dominant-baseline="central" font-size="{size}">{e(code)}</text>
  <line x1="46" y1="104" x2="114" y2="104" stroke="var(--fa)" stroke-width="1.4"/>
  <text class="st-arc"><textPath href="#st-bot" startOffset="50%" text-anchor="middle">{city}</textPath></text>
</svg>"""
    style = f"--f1:{f[0]};--f2:{f[1]};--f3:{f[2]};--fa:{accent}"
    return style, f'<div class="c-banner" aria-hidden="true"><div class="places">{places}</div>{stamp}</div>'



# ---------- path helpers ----------
def page_path(lang: str, slug: str | None = None) -> str:
    """Site-relative folder of a page, e.g. 'ur/study-in/italy/'."""
    base = "" if lang == "en" else "ur/"
    return base + (f"study-in/{slug}/" if slug else "")


def rel(from_path: str, to_path: str) -> str:
    """Relative link from one page folder to another path, so the site works under any base URL."""
    depth = from_path.count("/")
    return ("../" * depth) + to_path if (depth or to_path) else "./"


def lang_root(lang: str) -> str:
    return "" if lang == "en" else "ur/"


def service_path(lang: str, sid: str) -> str:
    return lang_root(lang) + f"services/{sid}/"


def countries_path(lang: str) -> str:
    return lang_root(lang) + "countries/"


def contact_path(lang: str) -> str:
    return lang_root(lang) + "contact/"


def services_all(lang: str) -> list[dict]:
    """The six main services plus English test coaching, each with its own page."""
    return UI[lang]["services"]["items"] + [UI[lang]["coaching"]["item"]]


def checker_path(lang: str) -> str:
    return ("" if lang == "en" else "ur/") + "eligibility/"


def wa_link(text: str) -> str:
    return f"https://wa.me/{WA}?text={quote(text)}"


# ---------- shared layout ----------
def layout(lang: str, here: str, title: str, desc: str, body: str, other_lang_path: str, extra_js: str = "") -> str:
    t = UI[lang]
    a = lambda p: rel(here, p)  # noqa: E731
    other = "ur" if lang == "en" else "en"
    fonts = ("family=Archivo:wdth,wght@75..125,500..800&family=Source+Sans+3:wght@400;600;700"
             "&family=JetBrains+Mono:wght@500;700")
    if lang == "ur":
        fonts += "&family=Noto+Nastaliq+Urdu:wght@400;600;700"
    socials = "".join(
        f'<a href="{u}" target="_blank" rel="noopener" aria-label="{n}"><svg><use href="#i-{i}"/></svg></a>'
        for n, i, u in SOCIAL)
    nav = t["nav"]
    home = a(page_path(lang))
    ld = {
        "@context": "https://schema.org", "@type": "LocalBusiness", "name": "M2M Global Consultants",
        "image": f"{SITE}/assets/logo.png", "url": f"{SITE}/", "telephone": PHONE_PK[1], "email": EMAIL,
        "address": {"@type": "PostalAddress",
                    "streetAddress": "Office 52, Mall of Lyallpur, Harrian Wala Chowk, D Ground, Block D, People's Colony No 1",
                    "addressLocality": "Faisalabad", "postalCode": "38000", "addressCountry": "PK"},
        "openingHours": "Mo-Sa 09:00-17:00", "sameAs": [u for _, _, u in SOCIAL],
    }
    popular = ["uk", "germany", "italy", "australia", "turkey", "hungary"]
    by_slug = {c["slug"]: c for c in COUNTRIES}
    foot_countries = "".join(
        f'<li><a href="{a(page_path(lang, s))}">{e(by_slug[s]["name"][lang])}</a></li>' for s in popular)
    foot_services = "".join(
        f'<li><a href="{a(service_path(lang, it["id"]))}">{e(it["title"])}</a></li>' for it in services_all(lang))
    return f"""<!doctype html>
<html lang="{lang}" dir="{t['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}/{here}">
<link rel="alternate" hreflang="en" href="{SITE}/{here if lang == 'en' else other_lang_path}">
<link rel="alternate" hreflang="ur" href="{SITE}/{here if lang == 'ur' else other_lang_path}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{SITE}/assets/logo.png">
<link rel="icon" href="{a('assets/icon.png')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fonts}&display=swap">
<link rel="stylesheet" href="{a('assets/style.css')}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
{ICONS}
<div class="topbar"><div class="wrap">
  <div class="tb-contacts">
    <a href="tel:{PHONE_PK[1]}" dir="ltr">{PHONE_PK[0]}</a>
    <a href="mailto:{EMAIL}">{EMAIL}</a>
    <span>{e(t['hours'])}</span>
  </div>
  <div class="tb-right">
    <a class="lang-switch" href="{a(other_lang_path)}" hreflang="{other}" lang="{other}">{e(t['switch_label'])}</a>
    <div class="socials" aria-label="Social media">{socials}</div>
  </div>
</div></div>
<header class="site"><div class="wrap">
  <a class="brand" href="{home}" aria-label="M2M Global Consultants"><img src="{a('assets/logo.png')}" alt="M2M Global Consultants" width="600" height="114"></a>
  <button class="menu-btn" id="menuBtn" aria-expanded="false" aria-controls="mainNav">{e(t['menu'])}</button>
  <nav class="main" id="mainNav" aria-label="Main">
    <a href="{home}#services">{e(nav['services'])}</a>
    <a href="{a(countries_path(lang))}">{e(nav['countries'])}</a>
    <a href="{a(service_path(lang, 'ielts-pte'))}">{e(nav['coaching'])}</a>
    <a href="{a(checker_path(lang))}">{e(nav['checker'])}</a>
    <a href="{a(contact_path(lang))}#faq">{e(nav['faq'])}</a>
    <a href="{a(contact_path(lang))}">{e(nav['contact'])}</a>
  </nav>
  <a class="btn btn-gold cta" href="https://wa.me/{WA}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg>{e(t['whatsapp'])}</a>
</div></header>
<main id="top">
{body}
</main>
<footer><div class="wrap">
  <div>
    <img class="logo-f" src="{a('assets/logo.png')}" alt="M2M Global Consultants" width="600" height="114">
    <p>{e(t['footer']['about'])}</p>
  </div>
  <div><h3>{e(t['footer']['services'])}</h3><ul>{foot_services}</ul></div>
  <div><h3>{e(t['footer']['countries'])}</h3><ul>{foot_countries}</ul></div>
  <div class="legal">
    <span>© <span id="yr">2026</span> {e(t['footer']['rights'])}</span>
    <span>{e(t['footer']['by'])} <a href="https://masmatixinnovations.co.uk" target="_blank" rel="noopener">Masmatix Innovations</a></span>
  </div>
</div></footer>
<a class="wa-float" href="https://wa.me/{WA}" target="_blank" rel="noopener" aria-label="WhatsApp"><svg><use href="#i-wa"/></svg></a>
<script src="{a('assets/site.js')}" defer></script>{extra_js}
</body>
</html>
"""


# ---------- components ----------
def country_card(c: dict, lang: str, here: str) -> str:
    t = UI[lang]["countries"]
    return (f'<a class="d" data-r="{c["region"]}" href="{rel(here, page_path(lang, c["slug"]))}">'
            f'<div class="top"><span class="iata" dir="ltr">{e(c["code"])}</span><span class="flag" dir="ltr">{e(c["label"])}</span></div>'
            f'<h3>{e(c["name"][lang])}</h3><p>{e(c["tagline"][lang])}</p>'
            f'<dl class="facts"><div><dt>{e(t["intakes"])}</dt><dd>{e(c["intakes"][lang])}</dd></div>'
            f'<div><dt>{e(t["scholarships"])}</dt><dd dir="auto">{e(c["scholarships"][0])}</dd></div></dl>'
            f'<span class="go">{e(t["view"])} <span aria-hidden="true">{"→" if lang == "en" else "←"}</span></span></a>')


def contact_section(lang: str, preset_country: str | None = None, preset_service: str | None = None) -> str:
    t = UI[lang]["contact"]
    opts = lambda items, sel=None: "".join(  # noqa: E731
        f'<option{" selected" if i == sel else ""}>{e(i)}</option>' for i in items)
    countries = [t["not_sure"]] + [c["name"][lang] for c in COUNTRIES] + [t["other"]]
    labels = {k: t[k] for k in ("f_name", "f_phone", "f_service", "f_country", "f_level", "f_mode", "f_msg")}
    return f"""<section id="contact" class="contact"><div class="wrap">
  <div class="info">
    <div class="sec-head" style="margin:0"><p class="eyebrow">{e(t['eyebrow'])}</p><h2>{e(t['title'])}</h2></div>
    <div class="info-row"><small>{e(t['office'])}</small><div>{e(t['address'])}</div><a class="note" href="https://www.google.com/maps/search/?api=1&amp;query=M2M+Global+Consultants+Mall+of+Lyallpur+Faisalabad" target="_blank" rel="noopener">{e(t['maps'])}</a></div>
    <div class="info-row"><small>{e(t['phone'])}</small><a href="tel:{PHONE_PK[1]}" dir="ltr">{PHONE_PK[0]}</a></div>
    <div class="info-row"><small>{e(t['uk'])}</small><a href="tel:{PHONE_UK[1]}" dir="ltr">{PHONE_UK[0]}</a><span class="note">{e(t['uk_note'])}</span></div>
    <div class="info-row"><small>{e(t['email'])}</small><a href="mailto:{EMAIL}">{EMAIL}</a></div>
    <div class="info-row"><small>{e(t['hours_label'])}</small><div>{e(t['hours'])}</div></div>
  </div>
  <form class="enquiry" id="enquiry" novalidate data-wa="{WA}" data-greeting="{e(t['greeting'])}" data-required="{e(t['f_required'])}" data-labels='{e(json.dumps(labels, ensure_ascii=False))}'>
    <div class="f"><label for="f-name">{e(t['f_name'])}</label><input id="f-name" name="name" autocomplete="name" required></div>
    <div class="f"><label for="f-phone">{e(t['f_phone'])}</label><input id="f-phone" name="phone" type="tel" autocomplete="tel" required dir="ltr"></div>
    <div class="f"><label for="f-service">{e(t['f_service'])}</label><select id="f-service" name="service">{opts(t['services'], preset_service)}</select></div>
    <div class="f"><label for="f-country">{e(t['f_country'])}</label><select id="f-country" name="country">{opts(countries, preset_country)}</select></div>
    <div class="f"><label for="f-level">{e(t['f_level'])}</label><select id="f-level" name="level">{opts(t['levels'])}</select></div>
    <div class="f"><label for="f-mode">{e(t['f_mode'])}</label><select id="f-mode" name="mode">{opts(t['modes'])}</select></div>
    <div class="f full"><label for="f-msg">{e(t['f_msg'])}</label><textarea id="f-msg" name="message" placeholder="{e(t['f_msg_ph'])}"></textarea></div>
    <p class="form-note">{e(t['f_note'])}</p>
    <div class="f full"><button class="btn btn-blue" type="submit"><svg><use href="#i-wa"/></svg>{e(t['f_submit'])}</button></div>
    <div class="wa-out" id="waOut" hidden>
      <b>{e(t['f_ready'])}</b><span class="note">{e(t['f_ready_note'])}</span>
      <a class="btn btn-gold" id="waLink" href="https://wa.me/{WA}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg>{e(t['f_open'])}</a>
    </div>
  </form>
</div></section>"""


# ---------- pages ----------
def home(lang: str) -> str:
    here = page_path(lang)
    t = UI[lang]
    h = t["hero"]
    L = t["land"]
    arrow = "→" if lang == "en" else "←"
    rows = "".join(
        f'<tr><td>{code}</td><td class="city">{e(city[lang])}</td><td>{e(route[lang])}</td>'
        f'<td><span class="st{" soon" if st == "study_only" else ""}">{e(h[st])}</span></td></tr>'
        for code, city, route, st in BOARD)
    trust = "".join(f'<div><b>{e(x)}</b><span>{e(y)}</span></div>' for x, y in t["trust"])
    cards = "".join(
        f'<a class="svc" href="{rel(here, service_path(lang, it["id"]))}"><span class="code" dir="ltr">{it["code"]}</span>'
        f'<h3>{e(it["title"])}</h3><p>{e(it["text"])}</p><span class="more">{e(L["more"])} <span aria-hidden="true">{arrow}</span></span></a>'
        for it in t["services"]["items"])
    groups = "".join(
        f'<div class="pill-group"><h3>{e(label)}</h3><div class="pills">'
        + "".join(f'<a class="mini" href="{rel(here, page_path(lang, c["slug"]))}"><span dir="ltr">{e(c["code"])}</span>{e(c["name"][lang])}</a>'
                  for c in COUNTRIES if c["region"] == key)
        + "</div></div>"
        for key, label in t["countries"]["regions"].items())
    steps = "".join(f"<li><h3>{e(x)}</h3><p>{e(y)}</p></li>" for x, y in L["steps"])
    why = "".join(f"<li><b>{e(x)}</b><span>{e(y)}</span></li>" for x, y in L["why"])
    c = t["contact"]
    maps = "https://www.google.com/maps/search/?api=1&amp;query=M2M+Global+Consultants+Faisalabad"
    body = f"""<section class="hero"><div class="wrap">
  <div>
    <p class="eyebrow eyebrow-gold">{e(h['eyebrow'])}</p>
    <h1>{e(h['title_a'])} <em>{e(h['title_em'])}</em> {e(h['title_b'])}</h1>
    <p class="lede">{e(h['lede'])}</p>
    <div class="hero-ctas"><a class="btn btn-gold" href="https://wa.me/{WA}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg>{e(t['whatsapp'])}</a><a class="btn btn-ghost" href="{rel(here, checker_path(lang))}">{e(L['find'])}</a></div>
    <div class="hero-facts"><span><b>★ 5.0</b> {e(h['fact1'])}</span><span>{e(h['fact2'])}</span></div>
  </div>
  <div class="board" aria-label="{e(h['board_title'])}">
    <div class="board-top"><span>{e(h['board_title'])}</span><strong dir="ltr">LYP</strong></div>
    <div class="board-scroll"><table><thead><tr>{''.join(f'<th>{e(x)}</th>' for x in h['board_cols'])}</tr></thead><tbody>{rows}</tbody></table></div>
    <p class="board-foot">{e(h['board_foot'])}</p>
  </div>
</div></section>
<div class="trust"><div class="wrap">{trust}</div></div>
<section id="services"><div class="wrap">
  <div class="sec-head"><p class="eyebrow">{e(t['services']['eyebrow'])}</p><h2>{e(t['services']['title'])}</h2><p class="lede">{e(t['services']['lede'])}</p></div>
  <div class="svc-grid">{cards}</div>
  <p class="also"><a href="{rel(here, service_path(lang, 'ielts-pte'))}">{e(L['also'])}</a></p>
</div></section>
<section id="destinations" class="dest"><div class="wrap">
  <div class="sec-head row-head"><div><p class="eyebrow">{e(t['countries']['eyebrow'])}</p><h2>{e(L['countries_title'])}</h2><p class="lede">{e(L['countries_lede'])}</p></div>
    <div class="row-ctas"><a class="btn btn-blue" href="{rel(here, countries_path(lang))}">{e(L['all_countries'])}</a><a class="btn btn-ghost-dark" href="{rel(here, checker_path(lang))}">{e(L['find'])}</a></div></div>
  <div class="pill-groups">{groups}</div>
</div></section>
<section><div class="wrap two-col">
  <div><p class="eyebrow">{e(t['process']['eyebrow'])}</p><h2>{e(L['steps_title'])}</h2><ol class="steps steps-4">{steps}</ol></div>
  <div><p class="eyebrow">{e(t['promise']['eyebrow'])}</p><h2>{e(L['why_title'])}</h2><ul class="why-list">{why}</ul>
    <a class="back" href="{maps}" target="_blank" rel="noopener">{e(L['reviews_link'])} {arrow}</a></div>
</div></section>
<section class="contact-band"><div class="wrap">
  <div><h2>{e(L['contact_title'])}</h2><p>{e(L['contact_lede'])}</p>
    <p class="cb-lines"><a href="tel:{PHONE_PK[1]}" dir="ltr">{PHONE_PK[0]}</a><span>{e(c['address'])}</span></p></div>
  <div class="row-ctas"><a class="btn btn-gold" href="https://wa.me/{WA}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg>{e(t['whatsapp'])}</a><a class="btn btn-ghost" href="{rel(here, contact_path(lang))}">{e(L['send'])}</a></div>
</div></section>"""
    title = "M2M Global Consultants" + (" | Study abroad, visa & travel consultants, Faisalabad" if lang == "en" else " | بیرونِ ملک تعلیم، ویزا اور سفری کنسلٹنٹس، فیصل آباد")
    return layout(lang, here, title, t["site_desc"], body, page_path("ur" if lang == "en" else "en"))


def countries_page(lang: str) -> str:
    here = countries_path(lang)
    t = UI[lang]
    ct = t["countries"]
    chips = f'<button type="button" class="chip on" data-f="all" aria-pressed="true">{e(ct["all"])} <span>{len(COUNTRIES)}</span></button>' + "".join(
        f'<button type="button" class="chip" data-f="{k}" aria-pressed="false">{e(v)} <span>{sum(1 for c in COUNTRIES if c["region"] == k)}</span></button>'
        for k, v in ct["regions"].items())
    cards = "\n".join(country_card(c, lang, here) for c in COUNTRIES)
    body = f"""<section class="c-hero"><div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{rel(here, page_path(lang))}">{e(t['country']['home'])}</a><span aria-hidden="true">/</span><span>{e(t['pages']['countries_crumb'])}</span></nav>
  <p class="eyebrow eyebrow-gold">{e(ct['eyebrow'])}</p>
  <h1>{e(ct['title'].format(n=len(COUNTRIES)))}</h1>
  <p class="lede">{e(ct['lede'])}</p>
</div></section>
<div class="check-band"><div class="wrap">
  <div><h2>{e(t['checker']['band_title'])}</h2><p>{e(t['checker']['band_text'])}</p></div>
  <a class="btn btn-gold" href="{rel(here, checker_path(lang))}">{e(t['checker']['band_cta'])}</a>
</div></div>
<section id="destinations" class="dest"><div class="wrap">
  <div class="filters" role="group" aria-label="{e(ct['eyebrow'])}">{chips}</div>
  <div class="dest-grid" id="destGrid">
{cards}
  </div>
</div></section>"""
    return layout(lang, here, f"{t['pages']['countries_title']} | M2M Global Consultants", ct["lede"], body,
                  countries_path("ur" if lang == "en" else "en"))


def service_page(it: dict, lang: str) -> str:
    here = service_path(lang, it["id"])
    t = UI[lang]
    st = t["service"]
    name = it["title"]
    if it["id"] == "ielts-pte":
        what = "".join(f'<li><span><b dir="ltr">{e(x)}</b> {e(y)}</span></li>' for x, y in t["coaching"]["tests"])
        lede = t["coaching"]["lede"]
    else:
        what = "".join(f"<li>{e(x)}</li>" for x in it["points"])
        lede = it["text"]
    steps = "".join(f"<li><h3>{e(x)}</h3><p>{e(y)}</p></li>" for x, y in t["land"]["steps"])
    faq_items = [t["faq"]["items"][i] for i in UI["faq_map"].get(it["id"], [])]
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(ans)}</p></details>" for q, ans in faq_items)
    faq_block = f'<h2>{e(st["faq"])}</h2><div class="faq">{faq}</div>' if faq else ""
    others = "".join(f'<a class="mini" href="{rel(here, service_path(lang, o["id"]))}"><span dir="ltr">{o["code"]}</span>{e(o["title"])}</a>'
                     for o in services_all(lang) if o["id"] != it["id"])
    extra = "".join(f'<li><span><b>{e(x)}</b> {e(y)}</span></li>' for x, y in t["services"]["extra"])
    student_link = ""
    if it["id"] in ("student-visa", "scholarships"):
        student_link = f'<div class="row-ctas btn-row"><a class="btn btn-blue" href="{rel(here, countries_path(lang))}">{e(t["land"]["all_countries"])}</a><a class="btn btn-ghost-dark" href="{rel(here, checker_path(lang))}">{e(t["land"]["find"])}</a></div>'
    services_opts = t["contact"]["services"]
    preset = next((o for o in services_opts if o.split(" /")[0].split(" ")[0] in name), None)
    body = f"""<section class="c-hero"><div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{rel(here, page_path(lang))}">{e(st['home'])}</a><span aria-hidden="true">/</span><a href="{rel(here, page_path(lang))}#services">{e(st['services'])}</a><span aria-hidden="true">/</span><span>{e(name)}</span></nav>
  <p class="eyebrow eyebrow-gold" dir="ltr">{it['code']} · {e(it['tag'])}</p>
  <h1>{e(name)}</h1>
  <p class="lede">{e(lede)}</p>
  <div class="hero-ctas"><a class="btn btn-gold" href="{wa_link(st['wa_text'].format(name=name))}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg>{e(st['cta'].format(name=name))}</a></div>
</div></section>
<section class="c-body"><div class="wrap c-grid">
  <div class="c-main">
    <h2>{e(st['what'])}</h2>
    <ul class="why">{what}</ul>
    {student_link}
    <h2>{e(st['how'])}</h2>
    <ol class="steps steps-4">{steps}</ol>
    {faq_block}
  </div>
  <aside class="c-side">
    <h2>{e(st['other'])}</h2>
    <div class="minis">{others}</div>
    <ul class="docs extra-list">{extra}</ul>
  </aside>
</div></section>
{contact_section(lang, preset_service=preset)}"""
    return layout(lang, here, f"{name} | M2M Global Consultants", lede, body,
                  service_path("ur" if lang == "en" else "en", it["id"]))


def contact_page(lang: str) -> str:
    here = contact_path(lang)
    t = UI[lang]
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(ans)}</p></details>" for q, ans in t["faq"]["items"])
    promise = "".join(f"<li><b>{e(x)}</b><span>{e(y)}</span></li>" for x, y in t["promise"]["items"])
    body = f"""<section class="c-hero"><div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{rel(here, page_path(lang))}">{e(t['country']['home'])}</a><span aria-hidden="true">/</span><span>{e(t['pages']['contact_crumb'])}</span></nav>
  <h1>{e(t['pages']['contact_title'])}</h1>
  <p class="lede">{e(t['land']['contact_lede'])}</p>
</div></section>
{contact_section(lang)}
<section id="faq"><div class="wrap two-col">
  <div><h2>{e(t['faq']['title'])}</h2><div class="faq">{faq}</div></div>
  <div><h2>{e(t['promise']['title'])}</h2><ul class="promise-list">{promise}</ul></div>
</div></section>"""
    return layout(lang, here, f"{t['pages']['contact_title']} | M2M Global Consultants", t["land"]["contact_lede"], body,
                  contact_path("ur" if lang == "en" else "en"))


def country_page(c: dict, lang: str) -> str:
    here = page_path(lang, c["slug"])
    t = UI[lang]["country"]
    name = c["name"][lang]
    region = UI[lang]["countries"]["regions"][c["region"]]
    home_p = rel(here, page_path(lang))
    li = lambda xs: "".join(f'<li dir="auto">{e(x)}</li>' for x in xs)  # noqa: E731
    steps = "".join(f"<li>{e(x)}</li>" for x in c["steps"][lang])
    docs = li(t["docs_common"] + c["docs"][lang])
    note = (f'<aside class="c-note"><b>{e(t["note"])}</b><p>{e(c["note"][lang])}</p></aside>' if c.get("note") else "")
    more = [x for x in COUNTRIES if x["region"] == c["region"] and x["slug"] != c["slug"]]
    more_links = "".join(f'<a class="mini" href="{rel(here, page_path(lang, x["slug"]))}"><span dir="ltr">{e(x["code"])}</span>{e(x["name"][lang])}</a>' for x in more)
    wa = wa_link(t["wa_text"].format(name=name))
    b_style, b_html = banner(c, lang)
    intro = BANNERS[c["slug"]]["intro"][lang]
    body = f"""<section class="c-hero has-banner" style="{b_style}"><div class="flagbar" aria-hidden="true"></div><div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{home_p}">{e(t['home'])}</a><span aria-hidden="true">/</span><a href="{rel(here, countries_path(lang))}">{e(t['countries'])}</a><span aria-hidden="true">/</span><span>{e(name)}</span></nav>
  {b_html}
  <div class="c-hero-grid">
    <div>
      <p class="eyebrow eyebrow-gold" dir="ltr">{e(c['code'])} · {e(c['label'])}</p>
      <h1>{e(t['title'].format(name=name))}</h1>
      <p class="lede">{e(intro)}</p>
      <div class="hero-ctas"><a class="btn btn-gold" href="{wa}" target="_blank" rel="noopener"><svg><use href="#i-wa"/></svg>{e(t['cta'].format(name=name))}</a></div>
    </div>
    <dl class="c-facts">
      <div><dt>{e(t['intakes'])}</dt><dd>{e(c['intakes'][lang])}</dd></div>
      <div><dt>{e(t['tests'])}</dt><dd><ul>{li(c['tests'])}</ul></dd></div>
      <div><dt>{e(t['scholarships'])}</dt><dd><ul>{li(c['scholarships'])}</ul></dd></div>
    </dl>
  </div>
</div></section>
<section class="c-body"><div class="wrap c-grid">
  <div class="c-main">
    <h2>{e(t['why'].format(name=name))}</h2>
    <ul class="why">{''.join(f'<li>{e(x)}</li>' for x in c['why'][lang])}</ul>
    <h2>{e(t['steps'])}</h2>
    <ol class="c-steps">{steps}</ol>
    {note}
  </div>
  <aside class="c-side">
    <h2>{e(t['docs'])}</h2>
    <ul class="docs">{docs}</ul>
    <p class="reviewed">{e(t['reviewed'])}</p>
  </aside>
</div></section>
<section class="c-more"><div class="wrap">
  <h2>{e(t['more'].format(region=region))}</h2>
  <div class="minis">{more_links}</div>
  <p><a class="back" href="{rel(here, countries_path(lang))}">{"←" if lang == "en" else "→"} {e(t['back'])}</a></p>
</div></section>
{contact_section(lang, preset_country=name)}"""
    title = f"{t['title'].format(name=name)} | M2M Global Consultants"
    desc = intro
    return layout(lang, here, title, desc, body, page_path("ur" if lang == "en" else "en", c["slug"]))


def checker_page(lang: str) -> str:
    here = checker_path(lang)
    t = UI[lang]["checker"]
    rules = load("eligibility.json")["rules"]
    opts = lambda items, sel=None: "".join(  # noqa: E731
        f'<option value="{v}"{" selected" if v == sel else ""}>{e(lbl)}</option>' for v, lbl in items)
    data = {
        "wa": WA,
        "text": {k: t[k] for k in ("results", "none", "labels", "reasons", "view", "wa", "wa_intro",
                                   "summary_labels", "disclaimer", "marks_invalid")},
        "countries": [{"slug": c["slug"], "code": c["code"], "name": c["name"][lang],
                       "url": rel(here, page_path(lang, c["slug"])), "rules": rules[c["slug"]]} for c in COUNTRIES],
    }
    how = "".join(f"<li>{e(x)}</li>" for x in t["how"])
    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    body = f"""<section class="c-hero"><div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{rel(here, page_path(lang))}">{e(UI[lang]['country']['home'])}</a><span aria-hidden="true">/</span><span>{e(t['eyebrow'])}</span></nav>
  <p class="eyebrow eyebrow-gold">{e(t['eyebrow'])}</p>
  <h1>{e(t['title'])}</h1>
  <p class="lede">{e(t['lede'])}</p>
</div></section>
<section class="checker-sec"><div class="wrap k-grid">
  <form class="k-form" id="checker" novalidate>
    <div class="f full"><label for="k-level">{e(t['level'])}</label><select id="k-level">{opts(t['levels'], 'master')}</select></div>
    <div class="f"><label for="k-marks">{e(t['marks'])}</label><input id="k-marks" type="number" inputmode="decimal" min="30" max="100" step="0.1" value="68" dir="ltr"><small class="hint">{e(t['marks_hint'])}</small></div>
    <div class="f"><label for="k-english">{e(t['english'])}</label><select id="k-english">{opts(t['eng_opts'], '6')}</select></div>
    <div class="f full chk"><input id="k-emi" type="checkbox" checked><label for="k-emi">{e(t['emi'])}</label></div>
    <div class="f"><label for="k-budget">{e(t['budget'])}</label><select id="k-budget">{opts(t['budgets'], '2')}</select></div>
    <div class="f"><label for="k-gap">{e(t['gap'])}</label><select id="k-gap">{opts(t['gaps'], '1')}</select></div>
    <div class="f full"><button class="btn btn-blue" type="submit">{e(t['submit'])}</button></div>
  </form>
  <aside class="k-how"><h2>{e(t['how_title'])}</h2><ul>{how}</ul></aside>
  <div class="k-results" id="results" hidden aria-live="polite"></div>
</div></section>
<script type="application/json" id="checker-data">{data_json}</script>"""
    return layout(lang, here, f"{t['title']} | M2M Global Consultants", t["lede"], body,
                  checker_path("ur" if lang == "en" else "en"),
                  extra_js=f'\n<script src="{rel(here, "assets/checker.js")}" defer></script>')


def not_found() -> str:
    body = """<section class="c-hero"><div class="wrap" style="padding-block:40px">
<h1>Page not found</h1><p class="lede">The page you are looking for has moved. Go back to the home page to see all services and countries.</p>
<div class="hero-ctas"><a class="btn btn-gold" href="./">Home</a></div></div></section>"""
    out = layout("en", "", "Page not found | M2M Global Consultants", UI["en"]["site_desc"], body, "ur/")
    # 404.html is served from any path, so use absolute-from-repo links via <base> is not portable; keep root-relative fallback
    return out


# ---------- build ----------
def write(path: str, content: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def main() -> None:
    for d in GENERATED:
        shutil.rmtree(ROOT / d, ignore_errors=True)
    (ROOT / "assets").mkdir()
    for f in ("style.css", "site.js", "checker.js", "logo.png", "icon.png"):
        shutil.copy(SRC / "assets" / f, ROOT / "assets" / f)

    pages = []
    for lang in ("en", "ur"):
        write(page_path(lang) + "index.html", home(lang))
        pages.append(page_path(lang))
        write(checker_path(lang) + "index.html", checker_page(lang))
        write(countries_path(lang) + "index.html", countries_page(lang))
        write(contact_path(lang) + "index.html", contact_page(lang))
        pages += [checker_path(lang), countries_path(lang), contact_path(lang)]
        for it in services_all(lang):
            write(service_path(lang, it["id"]) + "index.html", service_page(it, lang))
            pages.append(service_path(lang, it["id"]))
        for c in COUNTRIES:
            write(page_path(lang, c["slug"]) + "index.html", country_page(c, lang))
            pages.append(page_path(lang, c["slug"]))
    write("404.html", not_found())
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{SITE}/{p}</loc></url>\n" for p in pages) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print(f"Built {len(pages)} pages for {len(COUNTRIES)} countries.")


if __name__ == "__main__":
    main()
