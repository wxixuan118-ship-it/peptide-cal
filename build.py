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
SITE_NAME = "Peptide Calculator Pro"
SITE_ALT = "Peptide Calculator"
UPDATED = "2026-10-03"
BLOG_PUBLISHED = "2026-10-17"
BLOG_UPDATED = "2026-11-08"

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"

CALCULATOR_NAV = [
    ("/", "Peptide Calculator"),
    ("/peptide-reconstitution-calculator/", "Reconstitution Calculator"),
    ("/peptide-dosage-calculator/", "Dosage Calculator"),
    ("/peptide-blend-calculator/", "Blend Calculator"),
    ("/peptide-dilution-calculator/", "Dilution Calculator"),
    ("/peptide-concentration-calculator/", "Concentration Calculator"),
    ("/mg-to-ml-calculator/", "mg to mL Calculator"),
    ("/molarity-calculator/", "Molarity Calculator"),
    ("/bac-water-calculator/", "BAC Water Calculator"),
    ("/peptide-property-calculator/", "Peptide Property Calculator"),
    ("/peptide-molecular-weight-calculator/", "Molecular Weight Calculator"),
    ("/peptide-net-charge-calculator/", "Net Charge Calculator"),
    ("/retatrutide-peptide-calculator/", "Retatrutide"),
    ("/klow-peptide-calculator/", "KLOW"),
    ("/tdee-calculator/", "TDEE"),
]

CALCULATOR_GROUPS = [
    ("Peptide Calculators", CALCULATOR_NAV[:6]),
    ("Solutions & Conversions", CALCULATOR_NAV[6:9]),
    ("Research & Other Tools", CALCULATOR_NAV[9:]),
]

PAGES = [
    {
        "path": "/",
        "src": "home.html",
        "title": "Peptide Calculator – mg, mcg & IU to Syringe Units | Peptide Calculator Pro",
        "description": ("Peptide calculator for mg, mcg and IU vials: enter the vial strength, bacteriostatic "
                        "water and your dose to get exact U-100 syringe units, mL per injection and doses per vial."),
        "crumb": None,
        "app": "Peptide Calculator",
        "priority": "1.0",
        "updated": "2026-11-08",
    },
    {
        "path": "/peptide-reconstitution-calculator/",
        "src": "reconstitution.html",
        "title": "Peptide Reconstitution Calculator – Water Volume & Syringe Units",
        "description": ("Peptide reconstitution calculator: work backwards from the syringe units you want "
                        "to the bacteriostatic water volume to add, with mg/mL and dose checks."),
        "crumb": "Peptide Reconstitution Calculator",
        "app": "Peptide Reconstitution Calculator",
        "priority": "0.9",
        "updated": "2026-11-08",
    },
    {
        "path": "/peptide-dosage-calculator/",
        "src": "dosage.html",
        "title": "Peptide Dosage Calculator – Units, Doses per Vial & Supply",
        "description": ("Peptide dosage calculator: convert mcg or mg doses into U-100 syringe units, "
                        "then see doses per vial, days of supply and monthly peptide needs."),
        "crumb": "Peptide Dosage Calculator",
        "app": "Peptide Dosage Calculator",
        "priority": "0.9",
        "updated": "2026-11-08",
    },
    {
        "path": "/peptide-blend-calculator/",
        "src": "blend.html",
        "title": "Peptide Blend Calculator: Units for 2–3 Peptide Vials",
        "description": ("Peptide blend calculator for vials with two or three peptides: get the syringe units "
                        "for your dose and exactly how much of each peptide every draw delivers."),
        "crumb": "Peptide Blend Calculator",
        "app": "Peptide Blend Calculator",
        "priority": "0.9",
    },
    {
        "path": "/peptide-dilution-calculator/",
        "src": "dilution.html",
        "title": "Peptide Dilution Calculator: C1V1 = C2V2 for Vials",
        "description": ("Peptide dilution calculator: find how much stock solution and diluent to mix for "
                        "a weaker mg/mL or mcg/mL strength, and see your dose in units before and after."),
        "crumb": "Peptide Dilution Calculator",
        "app": "Peptide Dilution Calculator",
        "priority": "0.8",
        "updated": "2026-11-08",
    },
    {
        "path": "/peptide-concentration-calculator/",
        "src": "concentration.html",
        "title": "Peptide Concentration Calculator: mg/mL, mcg & Molarity",
        "description": ("Peptide concentration calculator: convert peptide mg and mL into mg/mL, mcg/mL, "
                        "mcg per syringe unit, % w/v and mM or µM from the molecular weight."),
        "crumb": "Peptide Concentration Calculator",
        "app": "Peptide Concentration Calculator",
        "priority": "0.8",
        "updated": "2026-11-08",
    },
    {
        "path": "/mg-to-ml-calculator/",
        "src": "mg-to-ml.html",
        "title": "Convert mg to mL – Calculator for Mass, Volume & Concentration",
        "description": "Convert mg to mL, or mL to mg, using a known concentration or density. See the formulas, worked examples and why mass and volume cannot convert directly.",
        "crumb": "mg to mL Calculator",
        "app": "Mass and Volume Calculator",
        "category": "EducationalApplication",
        "priority": "0.8",
        "updated": "2026-11-08",
    },
    {
        "path": "/bac-water-calculator/",
        "src": "bac-water.html",
        "title": "BAC Water Calculator – mg/mL, mcg per Unit & Diluent Volume",
        "description": "BAC water calculator: convert peptide mass and diluent volume into mg/mL, mcg per unit and a target-concentration volume, plus mg/mcg and mL/µL conversions.",
        "crumb": "BAC Water Calculator",
        "app": "BAC Water Calculator",
        "category": "EducationalApplication",
        "priority": "0.8",
        "updated": "2026-11-08",
    },
    {
        "path": "/molarity-calculator/",
        "src": "molarity.html",
        "title": "Molarity Calculator: Mass, Molecular Weight & Volume",
        "description": ("Free molarity calculator and molar concentration calculator. Convert mass or moles plus final volume to M, mM and µM, or calculate moles needed."),
        "crumb": "Molarity Calculator",
        "app": "Molarity Calculator",
        "category": "ScientificApplication",
        "priority": "0.8",
    },
    {
        "path": "/peptide-property-calculator/",
        "src": "peptide-property.html",
        "title": "Peptide Property Calculator: MW, pI & Net Charge",
        "description": ("Peptide property calculator: paste a sequence to get average and monoisotopic "
                        "molecular weight, length, net charge at any pH, isoelectric point and GRAVY."),
        "crumb": "Peptide Property Calculator",
        "app": "Peptide Property Calculator",
        "category": "ScientificApplication",
        "priority": "0.8",
        "updated": "2026-11-08",
    },
    {
        "path": "/peptide-molecular-weight-calculator/",
        "src": "molecular-weight.html",
        "title": "Peptide Molecular Weight Calculator: MW, Mass & m/z",
        "description": ("Peptide molecular weight calculator: paste a sequence to get average MW, monoisotopic "
                        "mass, formula and m/z ions, with acetyl, amide and disulfide options."),
        "crumb": "Peptide Molecular Weight Calculator",
        "app": "Peptide Molecular Weight Calculator",
        "category": "ScientificApplication",
        "priority": "0.8",
    },
    {
        "path": "/peptide-net-charge-calculator/",
        "src": "net-charge.html",
        "title": "Peptide Net Charge Calculator: pI, Charge at pH",
        "description": ("Peptide net charge calculator: enter a sequence and pH to get net charge, isoelectric "
                        "point (pI), GRAVY hydrophobicity and a solubility starting point."),
        "crumb": "Peptide Net Charge Calculator",
        "app": "Peptide Net Charge Calculator",
        "category": "ScientificApplication",
        "priority": "0.8",
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
        "updated": "2026-11-08",
    },
    {
        "path": "/klow-peptide-calculator/",
        "src": "klow.html",
        "title": "KLOW Peptide Calculator: 80 mg Blend Units & Doses",
        "description": ("KLOW peptide calculator for the 80 mg four-peptide blend: enter GHK-Cu, BPC-157, "
                        "TB-500 and KPV, then get the syringe units and what each draw delivers."),
        "crumb": "KLOW Peptide Calculator",
        "app": "KLOW Peptide Calculator",
        "priority": "0.8",
        "updated": "2026-11-08",
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
        "path": "/blog/", "src": "blog.html", "crumb": "Blog",
        "title": "Blog | Peptide Calculator Guides",
        "description": "Read clear, sourced guides to BAC water, peptide calculation terms, and unit conversions alongside our free calculators.",
        "updated": BLOG_UPDATED,
        "priority": "0.6",
    },
    {
        "path": "/blog/bac-water/", "src": "blog-bac-water.html", "crumb": "BAC Water",
        "parent_crumb": ("Blog", "/blog/"),
        "title": "BAC Water: Uses, Storage, Safety & Sterile Water Differences",
        "description": "What is BAC water? Learn what bacteriostatic water contains, how it differs from sterile water, what product labels say about storage, and key safety limits.",
        "article": True, "published": BLOG_PUBLISHED, "updated": BLOG_PUBLISHED,
        "priority": "0.7",
    },
    {
        "path": "/blog/how-much-bac-water-to-add/", "src": "blog-how-much-bac-water.html", "crumb": "How Much BAC Water to Add",
        "parent_crumb": ("Blog", "/blog/"),
        "title": "Peptide Calculator: How Much BAC Water to Add, With Worked Examples",
        "description": "How much BAC water to add to a peptide vial? See how water volume changes concentration and syringe units, with worked examples and a reverse formula.",
        "article": True, "published": BLOG_UPDATED, "updated": BLOG_UPDATED,
        "priority": "0.7",
    },
    {
        "path": "/blog/how-many-doses-per-vial/", "src": "blog-how-many-doses-per-vial.html", "crumb": "How Many Doses Per Vial",
        "parent_crumb": ("Blog", "/blog/"),
        "title": "Peptide Calculator: How Many Doses Per Vial and How Much to Inject",
        "description": "Work out how many doses per vial you get and what volume a dose equals in U-100 units. Plus who should answer how much you should take.",
        "article": True, "published": BLOG_UPDATED, "updated": BLOG_UPDATED,
        "priority": "0.7",
    },
    {
        "path": "/partners/", "src": "partners.html", "crumb": "Partners",
        "title": "Partners | Peptide Calculator",
        "description": "Partner websites and useful online tools recommended by Peptide Calculator.",
        "priority": "0.3",
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
<meta property="og:type" content="{og_type}">
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
    <nav class="site-nav" aria-label="Primary">
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
      <a href="/">Home</a>
      <a href="/peptide-reconstitution-calculator/">Reconstitution</a>
      <a href="/peptide-dosage-calculator/">Dosage</a>
      <a href="/peptide-concentration-calculator/">Concentration</a>
      <a href="/peptide-molecular-weight-calculator/">Molecular Weight</a>
      <a href="/blog/">Blog</a>
      <a href="/about/">About</a>
      <a href="/disclaimer/">Medical Disclaimer</a>
      <a href="/privacy/">Privacy</a>
      <a href="/partners/">Partners</a>
    </nav>
{partners}
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
    org_id = SITE_URL + "/#organization"
    org = {
        "@type": "Organization", "@id": org_id,
        "name": SITE_NAME, "alternateName": SITE_ALT,
        "url": SITE_URL + "/",
        "logo": {"@type": "ImageObject", "url": SITE_URL + "/assets/img/favicon.svg"},
        "sameAs": [p[0] for p in PARTNERS if isinstance(p, tuple)],
    }
    graph = [org, {
        "@type": "WebSite", "@id": SITE_URL + "/#website",
        "url": SITE_URL + "/", "name": SITE_NAME, "alternateName": SITE_ALT,
        "inLanguage": "en", "publisher": {"@id": org_id},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": SITE_URL + "/?q={search_term_string}"},
            "query-input": "required name=search_term_string",
        },
    }]
    page_node = {
        "@type": "WebPage", "@id": url + "#webpage", "url": url, "name": page["title"],
        "description": page["description"], "isPartOf": {"@id": SITE_URL + "/#website"},
        "dateModified": page.get("updated", UPDATED), "inLanguage": "en",
        "author": {"@id": org_id}, "publisher": {"@id": org_id},
        "medicalReviewer": {
            "@type": "Organization",
            "name": "Peptide Calculator Pro Medical Review Team",
        },
    }
    if page["path"] == "/":
        page_node["speakable"] = {
            "@type": "SpeakableSpecification",
            "cssSelector": [".steps", ".formula", "#faq h3", "#faq p"],
        }
    graph.append(page_node)
    if page.get("app"):
        features = page.get("features")
        if features is None:
            features = [
                "Convert mg or mcg vial strength to U-100 syringe units",
                "Enter bacteriostatic water volume to get mg per mL concentration",
                "Support for IU-labelled vials using the product's own IU-per-mg figure",
                "Show mL per injection, doses per vial and days of supply",
                "Works for single peptides and multi-peptide blends",
            ]
        graph.append({
            "@type": "WebApplication", "@id": url + "#app", "name": page["app"], "url": url,
            "applicationCategory": page.get("category", "HealthApplication"), "operatingSystem": "Any (web browser)",
            "browserRequirements": "Requires JavaScript for live recalculation",
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "description": page["description"],
            "provider": {"@id": org_id},
            "featureList": features,
        })
        page_node["mainEntity"] = {"@id": url + "#app"}
    if page.get("article"):
        graph.append({
            "@type": "Article", "@id": url + "#article", "headline": page["title"],
            "description": page["description"], "url": url,
            "datePublished": page["published"], "dateModified": page.get("updated", UPDATED),
            "author": {"@id": org_id}, "publisher": {"@id": org_id},
            "mainEntityOfPage": {"@id": url + "#webpage"},
        })
        page_node["mainEntity"] = {"@id": url + "#article"}
    crumbs = [{"@type": "ListItem", "position": 1, "name": SITE_NAME, "item": SITE_URL + "/"}]
    if page.get("parent_crumb"):
        label, path = page["parent_crumb"]
        crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1,
                       "name": label, "item": SITE_URL + path})
    if page.get("crumb"):
        crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1,
                       "name": page["crumb"], "item": url})
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


# Partner badges, shown in one horizontal row in the home-page footer only.
PARTNERS = [
    ('https://smollaunch.com', 'https://smollaunch.com/badges/featured.svg',
     'Peptide Calculator \u2014 Featured on Smol Launch', 250, 60),
    ('https://fazier.com/launches/peptidecalculatorpro.org',
     'https://fazier.com/api/v1//public/badges/launch_badges.svg?badge_type=launched&theme=light',
     'Peptide Calculator \u2014 Launched on Fazier', 120, 51),
    ('https://twelve.tools', 'https://twelve.tools/badge0-white.svg',
     'Featured on Twelve Tools', 148, 40),
    ('https://unitelist.com/product/peptidecalculatorpro',
     'https://unitelist.com/assets/images/badge.png', 'Unite List', 166, 54),
    ('https://www.freeai.run', 'https://www.freeai.run/badge/badge_light.svg',
     'Featured on FreeAI', 200, 54),
    ('https://findly.tools/peptide-calculator-pro?utm_source=peptide-calculator-pro',
     'https://findly.tools/badges/findly-tools-badge-light.svg',
     'Featured on Findly.tools', 175, 55),
    ('https://saascity.io', 'https://saascity.io/badges/featured-dark.svg',
     'Featured on SaaSCity', 150, 54),
    ('https://newname.ai/badge?ref=peptide-calculator-pro',
     'https://newname.ai/badge/listed.svg', 'Listed on NewName.ai',
     200, 54, ' data-newname-badge="peptide-calculator-pro"'),
    ('https://prolaunch.net', 'https://prolaunch.net/images/badges/featured-light.svg',
     'Pro Launch Featured Badge (light theme)', 152, 44,
     ' title="Pro Launch Featured Badge"'),
    ('https://shinylaunch.com/product/peptidecalculatorpro',
     'https://shinylaunch.com/assets/images/badge.png', 'ShinyLaunch', 198, 54),
    ('https://thekeytools.com/ai/peptidecalculatorpro',
     'https://thekeytools.com/assets/images/badge.png', 'The Key Tools', 208, 54),
    ('https://devhub.best/projects/peptide-calculator?utm_source=badge',
     'https://r2.direasy-multi-tenant.focusapps.app/uploads/616d0b1a-3979-4b8c-94d1-b4f1fedd3ead/1783239702078/53yqmim54zv/featured-on-light.svg',
     'Featured on DevHub', 150, 44),
    ('https://dododirectory.com', 'https://dododirectory.com/badge-light.png',
     'Featured on DodoDirectory', 200, 54),
    ('https://huntfortools.com/tool/peptidecalculatorpro',
     'https://huntfortools.com/assets/images/badge.png', 'Hunt for Tools', 207, 54),
    ('https://productwing.com/product/peptidecalculatorpro',
     'https://productwing.com/assets/images/badge.png', 'Product Wing', 202, 54),
    ('https://indielineup.com/product/peptide-calculator?ref=badge',
     'https://indielineup.com/badge/peptide-calculator.svg',
     'Featured on IndieLineup', 160, 44),
    ('https://startupbenchmarks.com/product/peptidecalculatorpro',
     'https://startupbenchmarks.com/assets/images/badge.png',
     'Startup Benchmarks', 265, 54),
    # Exact markup required by directory backlink verifiers. Do not route
    # these through the tuple template.
    '<a href="https://toolfame.com" target="_blank" rel="noopener"><img src="https://toolfame.com/badge-light.svg" alt="Featured on toolfame.com" loading="lazy" width="160" height="54"></a>',
    '<a href="https://launchigniter.com" target="_blank" rel="noopener"><img src="https://launchigniter.com/badge.svg" alt="Featured on LaunchIgniter" loading="lazy" width="250" height="54"></a>',
    '<a href="https://goodsaas.xyz/saas/peptidecalculatorpro" target="_blank" rel="noopener"><img src="https://goodsaas.xyz/badge/peptidecalculatorpro.svg?theme=light" alt="Featured on GoodSaaS" loading="lazy" width="154" height="32"></a>',
]


def partners_html():
    links = []
    for partner in PARTNERS:
        if isinstance(partner, str):
            links.append("      " + partner)
            continue
        links.append(
            '      <a href="%s" target="_blank" rel="noopener"%s>'
            '<img src="%s" alt="%s" loading="lazy"%s%s></a>' % (
                partner[0], partner[5] if len(partner) > 5 else '',
                html.escape(partner[1]), html.escape(partner[2]),
                ' width="%d"' % partner[3] if partner[3] is not None else '',
                ' height="%d"' % partner[4] if partner[4] is not None else '')
        )
    return '    <div class="partners" aria-label="Partners">\n%s\n    </div>' % "\n".join(links)


def render(page):
    body = (SRC / page["src"]).read_text(encoding="utf-8")
    body = re.sub(r"\{\{SYRINGE (\d+(?:\.\d+)?)\}\}", lambda m: syringe_svg(float(m.group(1))), body)
    url = SITE_URL + page["path"]
    calculator_groups = "\n".join(
        '          <div class="nav-group"><h2>%s</h2>%s</div>' % (
            html.escape(heading), "".join(
                '<a href="%s"%s>%s</a>' % (
                    href, ' aria-current="page"' if href == page["path"] else "", html.escape(label))
                for href, label in links))
        for heading, links in CALCULATOR_GROUPS
    )
    nav = ('      <details class="nav-menu">\n'
           '        <summary>Calculators</summary>\n'
           '        <div class="nav-menu-panel">\n%s\n        </div>\n'
           '      </details>\n'
           '      <a href="/blog/"%s>Blogs</a>' % (
               calculator_groups,
               ' aria-current="page"' if page["path"].startswith("/blog/") else ""))
    crumbs = ""
    if page.get("crumb"):
        parent = ""
        if page.get("parent_crumb"):
            label, path = page["parent_crumb"]
            parent = ' &rsaquo; <a href="%s">%s</a>' % (path, html.escape(label))
        crumbs = ('<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Peptide Calculator</a>%s '
                  '&rsaquo; <span>%s</span></nav>' % (parent, html.escape(page["crumb"])))
    return TEMPLATE.format(
        title=html.escape(page["title"]), description=html.escape(page["description"]),
        url=url, site_name=SITE_NAME, og_type="article" if page.get("article") else "website",
        schema=build_schema(page, body, url), nav=nav,
        crumbs=crumbs, body=body.strip(), updated=page.get("updated", UPDATED),
        partners=partners_html() if page["path"] == "/" else "", css_v=asset_version("style.css"),
        script=('<script type="module" src="/assets/mass-volume.js?v=%s"></script>' % asset_version("mass-volume.js")
                if page["path"] == "/mg-to-ml-calculator/" else
                '<script type="module" src="/assets/bac-water.mjs?v=%s"></script>' % asset_version("bac-water.mjs")
                if page["path"] == "/bac-water-calculator/" else
                '<script src="/assets/calc.js?v=%s" defer></script>' % asset_version("calc.js") if page.get("app") else ""),
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
        % (SITE_URL, p["path"], p.get("updated", UPDATED), p["priority"]) for p in PAGES)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % urls,
        encoding="utf-8")


if __name__ == "__main__":
    main()
