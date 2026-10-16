# M2M Global Consultants website

Website for **M2M Global Consultants**, study abroad and visa consultants in Faisalabad, Pakistan.
Live preview: https://mhkhan50.github.io/m2m-website/

- 70 pages: home + 34 country guides, in **English** and **Urdu** (right-to-left)
- Static HTML, no framework at runtime, fast on mobile
- WhatsApp enquiry form (no server needed)
- SEO: canonical and hreflang links, LocalBusiness schema, sitemap

## How it works

The pages are generated from data by a small Python script with no dependencies.

```
src/
  build.py              # the generator
  data/countries.json   # one record per country (English + Urdu)
  data/ui.json          # all interface text (English + Urdu)
  assets/               # style.css, site.js, logo, icons
```

To change content, edit the JSON files and rebuild:

```bash
python3 src/build.py
```

The script writes `index.html`, `study-in/<country>/`, `ur/…`, `assets/`, `sitemap.xml` and `robots.txt`
into the repository root, which GitHub Pages serves from the `main` branch.

## Custom domain

When `m2mglobalconsultants.com` points to GitHub Pages, add a `CNAME` file containing the domain and set it in
**Settings → Pages → Custom domain**.

---
Website by [Masmatix Innovations](https://masmatixinnovations.co.uk).
