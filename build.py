#!/usr/bin/env python3
"""Static build for the peptide calculator site.

    python3 build.py            -> writes the site to ./dist

Page bodies live in ./src/*.html; this script wraps them with the shared <head>,
navigation, footer and JSON-LD, so every page is fully server-rendered HTML.
Change SITE_URL once before deploying.
"""
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

SITE_URL = "https://peptidecalculatorpro.org"   # <- your production domain, no trailing slash
SITE_NAME = "Peptide Calculator"
UPDATED = "2026-10-01"

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"

NAV = [
    ("/", "Peptide Calculator"),
    ("/peptide-reconstitution-calculator/", "Reconstitution Calculator"),
    ("/peptide-dosage-calculator/", "Dosage Calculator"),
    ("/retatrutide-peptide-calculator/", "Retatrutide"),
    ("/tdee-calculator/", "TDEE"),
]

PAGES = [
    {
        "path": "/",
        "src": "home.html",
        "title": "Peptide Calculator: Free mg to Syringe Units Tool",
        "description": ("Free peptide calculator: enter vial mg, bacteriostatic water and your dose "
                        "to get exact syringe units, mL per injection and doses per vial. Instant results."),
        "crumb": None,
        "app": "Peptide Calculator",
        "priority": "1.0",
    },
    {
        "path": "/peptide-reconstitution-calculator/",
        "src": "reconstitution.html",
        "title": "Peptide Reconstitution Calculator: BAC Water Mixing",
        "description": ("Peptide reconstitution calculator: find how much bacteriostatic water to add "
                        "to any vial so each dose lands on a clean, easy-to-read syringe unit mark."),
        "crumb": "Peptide Reconstitution Calculator",
        "app": "Peptide Reconstitution Calculator",
        "priority": "0.9",
    },
    {
        "path": "/peptide-dosage-calculator/",
        "src": "dosage.html",
        "title": "Peptide Dosage Calculator: Dose, Units & Vial Supply",
        "description": ("Peptide dosage calculator: turn any mcg or mg dose into syringe units and mL, "
                        "then see doses per vial, how long a vial lasts and monthly needs."),
        "crumb": "Peptide Dosage Calculator",
        "app": "Peptide Dosage Calculator",
        "priority": "0.9",
    },
    {
        "path": "/retatrutide-peptide-calculator/",
        "src": "retatrutide.html",
        "title": "Retatrutide Peptide Calculator: mg to Syringe Units",
        "description": ("Retatrutide peptide calculator: convert vial mg, bacteriostatic water and a "
                        "prescribed dose into U-100 syringe units and mL. Math only, no dose advice."),
        "crumb": "Retatrutide Peptide Calculator",
        "app": "Retatrutide Peptide Calculator",
        "priority": "0.8",
    },
    {
        "path": "/tdee-calculator/",
        "src": "tdee.html",
        "title": "TDEE Calculator with Steps & Adaptive TDEE",
        "description": ("Free TDEE calculator with steps and an adaptive mode: estimate daily calorie burn, "
                        "then get weight-loss targets and a protein range in seconds."),
        "crumb": "TDEE Calculator",
        "app": "TDEE Calculator",
        "priority": "0.8",
    },
    {
        "path": "/about/", "src": "about.html", "crumb": "About",
        "title": "About Peptide Calculator | How Our Math Is Checked",
        "description": ("Who builds Peptide Calculator, how every formula is checked, and what the "
                        "calculators can and cannot tell you about reconstitution and dosing."),
        "priority": "0.3",
    },
    {
        "path": "/disclaimer/", "src": "disclaimer.html", "crumb": "Medical Disclaimer",
        "title": "Medical Disclaimer | Peptide Calculator",
        "description": ("Peptide Calculator provides arithmetic for educational purposes only. It is not "
                        "medical advice, a prescription or a recommendation to use any compound."),
        "priority": "0.3",
    },
    {
        "path": "/privacy/", "src": "privacy.html", "crumb": "Privacy Policy",
        "title": "Privacy Policy | Peptide Calculator",
        "description": ("Peptide Calculator runs entirely in your browser. We do not store the numbers you "
                        "type, require an account or sell personal data. Read the full policy."),
        "priority": "0.2",
    },
]

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{site_name}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#0b7a75">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/style.css?v={css_v}">
<script type="application/ld+json">
{schema}
</script>
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/"><span class="brand-mark" aria-hidden="true">P</span>{site_name}</a>
    <nav class="site-nav" aria-label="Calculators">
{nav}
    </nav>
  </div>
</header>
<main class="wrap">
{crumbs}
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <nav aria-label="Footer">
      <a href="/">Peptide Calculator</a>
      <a href="/peptide-reconstitution-calculator/">Peptide Reconstitution Calculator</a>
      <a href="/peptide-dosage-calculator/">Peptide Dosage Calculator</a>
      <a href="/retatrutide-peptide-calculator/">Retatrutide Peptide Calculator</a>
      <a href="/tdee-calculator/">TDEE Calculator</a>
      <a href="/about/">About</a>
      <a href="/disclaimer/">Medical Disclaimer</a>
      <a href="/privacy/">Privacy</a>
    </nav>
    <p>Educational tool only — not medical advice. Always confirm doses with a licensed healthcare professional. Last reviewed {updated}.</p>
  </div>
</footer>
{script}
</body>
</html>
"""


def strip_tags(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s))).strip()


def syringe_svg(units, capacity=100):
    """Server-rendered syringe so the default result is visible before JS runs."""
    x0, w = 30, 300
    pct = max(0.0, min(units / capacity, 1.0))
    step = 10 if capacity == 100 else 5
    ticks = []
    for u in range(0, capacity + 1, step):
        x = x0 + w * u / capacity
        major = u % (step * 2) == 0
        ticks.append('<line class="tick" x1="%g" y1="14" x2="%g" y2="%d"/>' % (x, x, 26 if major else 22))
        if major:
            ticks.append('<text class="tick-label" x="%g" y="62" text-anchor="middle">%d</text>' % (x, u))
    return (
        '<div class="syringe" aria-hidden="true">'
        '<svg viewBox="0 0 360 70" role="presentation">'
        '<rect class="barrel" x="30" y="12" width="300" height="34" rx="5" stroke-width="1.5"/>'
        '<rect class="fill" x="31" y="13" width="%.1f" height="32"/>'
        '<rect class="plunger" x="%.1f" y="8" width="5" height="42"/>'
        '<rect class="plunger" x="2" y="26" width="28" height="6"/>'
        '<g class="ticks" data-cap="%d">%s</g>'
        "</svg></div>" % (w * pct, x0 + w * pct, capacity, "".join(ticks))
    )


def faq_items(body):
    sec = re.search(r'<section[^>]*id="faq"[^>]*>(.*?)</section>', body, re.S)
    if not sec:
        return []
    pairs = re.findall(r"<h3>(.*?)</h3>\s*((?:<p>.*?</p>\s*)+)", sec.group(1), re.S)
    return [(strip_tags(q), strip_tags(a)) for q, a in pairs]


def build_schema(page, body, url):
    graph = [{
        "@type": "WebSite", "@id": SITE_URL + "/#website",
        "url": SITE_URL + "/", "name": SITE_NAME, "inLanguage": "en",
    }]
    page_node = {
        "@type": "WebPage", "@id": url + "#webpage", "url": url, "name": page["title"],
        "description": page["description"], "isPartOf": {"@id": SITE_URL + "/#website"},
        "dateModified": UPDATED, "inLanguage": "en",
    }
    graph.append(page_node)
    if page.get("app"):
        graph.append({
            "@type": "WebApplication", "@id": url + "#app", "name": page["app"], "url": url,
            "applicationCategory": "HealthApplication", "operatingSystem": "Any (web browser)",
            "browserRequirements": "Requires JavaScript for live recalculation",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "description": page["description"],
        })
        page_node["mainEntity"] = {"@id": url + "#app"}
    crumbs = [{"@type": "ListItem", "position": 1, "name": SITE_NAME, "item": SITE_URL + "/"}]
    if page.get("crumb"):
        crumbs.append({"@type": "ListItem", "position": 2, "name": page["crumb"], "item": url})
    graph.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": crumbs})
    page_node["breadcrumb"] = {"@id": url + "#breadcrumb"}
    faqs = faq_items(body)
    if faqs:
        graph.append({
            "@type": "FAQPage", "@id": url + "#faq",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs],
        })
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2, ensure_ascii=False)


def asset_version(name):
    """Short content hash so browsers fetch fresh CSS/JS after every deploy."""
    return hashlib.md5((ROOT / "assets" / name).read_bytes()).hexdigest()[:8]


def render(page):
    body = (SRC / page["src"]).read_text(encoding="utf-8")
    body = re.sub(r"\{\{SYRINGE (\d+(?:\.\d+)?)\}\}", lambda m: syringe_svg(float(m.group(1))), body)
    url = SITE_URL + page["path"]
    nav = "\n".join(
        '      <a href="%s"%s>%s</a>' % (href, ' aria-current="page"' if href == page["path"] else "", label)
        for href, label in NAV
    )
    crumbs = ""
    if page.get("crumb"):
        crumbs = ('<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Peptide Calculator</a> '
                  "&rsaquo; <span>%s</span></nav>" % page["crumb"])
    return TEMPLATE.format(
        title=html.escape(page["title"]), description=html.escape(page["description"]),
        url=url, site_name=SITE_NAME, schema=build_schema(page, body, url), nav=nav,
        crumbs=crumbs, body=body.strip(), updated=UPDATED, css_v=asset_version("style.css"),
        script='<script src="/assets/calc.js?v=%s" defer></script>' % asset_version("calc.js") if page.get("app") else "",
    )


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(ROOT / "assets", DIST / "assets")
    for page in PAGES:
        out = DIST / page["path"].strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(page), encoding="utf-8")
        print("built", page["path"])
    (DIST / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL, encoding="utf-8")
    urls = "".join(
        "  <url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n"
        % (SITE_URL, p["path"], UPDATED, p["priority"]) for p in PAGES)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % urls,
        encoding="utf-8")


if __name__ == "__main__":
    main()
