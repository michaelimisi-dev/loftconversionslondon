"""Build the static site in site/ from the page files in content/.

Each content file is a JSON front-matter block between two "---" lines,
followed by the HTML that goes inside <main>. The output path mirrors the
content path: content/services/dormer-loft-conversion.html is written to
site/services/dormer-loft-conversion.html and served at
/services/dormer-loft-conversion.

Front-matter keys:
  title, description   required
  h1                   used only for checks; the body supplies the visible <h1>
  breadcrumbs          [["Home", "/"], ["Services", "/#services"], ["Dormer", null]]
  service              {"name": ..., "type": ..., "description": ..., "area": "London"}
  faq                  [["Question?", "Plain-text answer."], ...]
  faq_heading          heading for the FAQ section
  cta_heading, cta_text  override the closing call to action
  sitemap              {"changefreq": "monthly", "priority": "0.8"}; omit to exclude
  area                 location pages only: the borough name, e.g. "Wandsworth"

Location pages live at content/<service-slug>/<area-slug>.html and are served
at /<service-slug>/<area-slug>.

Body placeholders:
  {{FORM:<source>:<heading>}}   a quote form
  {{HOW_IT_WORKS}}              the four-step process section
  {{LOCATIONS:<service-slug>}}  links to that service's location pages (service pages)
  {{SIBLINGS}}                  <li> links to the same service in other areas (location pages)

Run:  python tools/build.py
"""

import datetime
import html
import json
import pathlib
import re
import sys

# ---------------------------------------------------------------------------
# Site settings. Change these and rebuild to update every page at once.
# ---------------------------------------------------------------------------
SITE = {
    "domain": "loftconversionslondon.co.uk",
    "name": "Loft Conversions London",
    "email": "info@loftconversionslondon.co.uk",
    # PHONE PLACEHOLDER: set both values, e.g. "+442012345678" and "020 1234 5678".
    "phone_e164": None,
    "phone_display": None,
    # GA4 PLACEHOLDER: replace with the real measurement ID.
    "ga4_id": "G-XXXXXXXXXX",
    "hours": "Monday to Friday: 8am to 6pm",
}

SERVICES = [
    ("dormer-loft-conversion", "Dormer loft conversion", "Dormer"),
    ("hip-to-gable-loft-conversion", "Hip-to-gable loft conversion", "Hip-to-Gable"),
    ("mansard-loft-conversion", "Mansard loft conversion", "Mansard"),
    ("velux-loft-conversion", "Velux loft conversion", "Velux"),
    ("l-shaped-dormer-loft-conversion", "L-shaped dormer loft conversion", "L-Shaped Dormer"),
    ("loft-pod-conversion", "Loft pod conversion", "Loft Pod"),
    ("loft-bathroom-conversion", "Loft bathroom or en-suite", "Loft Bathroom &amp; En-Suite"),
    ("loft-kitchen-conversion", "Loft kitchen conversion", "Loft Kitchen"),
    ("basement-conversion", "Basement conversion", "Basement Conversion"),
    ("bungalow-loft-conversion", "Bungalow loft conversion", "Bungalow"),
    ("mansion-block-loft-conversion", "Mansion block or flat loft conversion", "Mansion Block &amp; Flat"),
    ("loft-conversion-roof-terrace", "Loft with roof terrace or balcony", "Roof Terrace &amp; Balcony"),
]

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
OUT = ROOT / "site"
BUILD_DATE = datetime.date.today().isoformat()


def base_url():
    return "https://" + SITE["domain"]


def page_url(rel):
    """content-relative path -> public URL path."""
    rel = rel.as_posix()
    if rel == "index.html":
        return "/"
    return "/" + rel[: -len(".html")]


# ---------------------------------------------------------------------------
# Shared fragments
# ---------------------------------------------------------------------------
PHONE_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20 15.5c-1.25 0-2.45-.2-3.57-.57a1 1 0 0 0-1.02.24l-2.2 2.2a15.05 15.05 0 0 1-6.59-6.58l2.2-2.21a1 1 0 0 0 .25-1.02A11.36 11.36 0 0 1 8.5 4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1 17 17 0 0 0 17 17 1 1 0 0 0 1-1v-3.5a1 1 0 0 0-1-1z"/></svg>'


def header(quote_href):
    if SITE["phone_e164"]:
        action = (
            f'<a href="tel:{SITE["phone_e164"]}" class="header-call" aria-label="Call {SITE["name"]}">'
            f'{PHONE_ICON}<span>{SITE["phone_display"]}</span></a>'
        )
    else:
        action = f'<a href="{quote_href}" class="btn btn-primary header-cta"><span class="hide-sm">Get a</span>Free Quote</a>'
    return f"""<div class="announcement-bar">
  Free loft survey and fixed written quote across all 32 London boroughs
</div>

<header class="site-header">
  <div class="container">
    <a href="/" class="logo" aria-label="{SITE["name"]} home">Loft Conversions <span>London</span></a>
    <nav aria-label="Primary">
      <a href="/#services">Services</a>
      <a href="/#prices">Prices</a>
      <a href="/about">About</a>
      <a href="/contact">Contact</a>
    </nav>
    {action}
  </div>
</header>"""


def service_options():
    opts = ['<option value="">Select a service</option>']
    opts += [f"<option>{label}</option>" for _, label, _ in SERVICES]
    opts.append("<option>Not sure yet</option>")
    return "\n              ".join(opts)


_form_count = 0


def quote_form(source, heading):
    """A FormSubmit lead form. The first form on a page gets id="quote" so header buttons can jump to it."""
    global _form_count
    _form_count += 1
    form_id = "quote" if _form_count == 1 else f"quote-{_form_count}"
    tag = "h2" if _form_count == 1 else "h3"
    return f"""<form id="{form_id}" class="lead-form" action="https://formsubmit.co/ajax/{SITE["email"]}" method="POST" data-lead-form>
        <{tag}>{heading}</{tag}>
        <input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
        <input type="hidden" name="_subject" value="New {SITE["name"]} lead">
        <input type="hidden" name="_captcha" value="false">
        <input type="hidden" name="_template" value="table">
        <input type="hidden" name="source_page" value="{html.escape(source)}">
        <div class="form-row">
          <label>Name<input type="text" name="name" required autocomplete="name"></label>
          <label>Phone<input type="tel" name="phone" required inputmode="tel" autocomplete="tel"></label>
          <label>Type of conversion
            <select name="service" required>
              {service_options()}
            </select>
          </label>
          <label>Postcode<input type="text" name="postcode" autocomplete="postal-code"></label>
        </div>
        <button type="submit" class="btn btn-primary">Get a Free Quote</button>
        <!-- BUSINESS CLAIM: confirm the call-back time with the builder -->
        <p class="form-note">No obligation. We call you back within one working day.</p>
      </form>"""


HOW_IT_WORKS = """<section class="alt" aria-labelledby="how-heading">
    <div class="container">
      <div class="section-intro">
        <p class="overline">How it works</p>
        <h2 id="how-heading">Your Loft Conversion, Step by Step</h2>
      </div>
      <ol class="steps">
        <li>
          <h3>Free survey</h3>
          <p>We visit, measure the loft and roof, check head height and talk through how you want to use the space.</p>
        </li>
        <li>
          <h3>Design and approvals</h3>
          <p>Drawings, structural calculations, planning or a lawful development certificate, and party wall notices.</p>
        </li>
        <li>
          <h3>The build</h3>
          <p>Scaffolding goes up, the roof and floor are built from outside, and the staircase goes in near the end.</p>
        </li>
        <li>
          <h3>Sign-off and handover</h3>
          <p>Building control's final inspection, your completion certificate, and a finished room ready to use.</p>
        </li>
      </ol>
    </div>
  </section>"""


def breadcrumbs_html(crumbs):
    items = []
    for name, url in crumbs:
        if url:
            items.append(f'<a href="{url}">{name}</a>')
        else:
            items.append(f'<span aria-current="page">{name}</span>')
    return f"""<nav class="breadcrumbs" aria-label="Breadcrumb">
    <div class="container">{" / ".join(items)}</div>
  </nav>"""


def faq_html(faq, heading):
    items = "\n".join(
        f"""      <details>
        <summary>{html.escape(q)}</summary>
        <p>{html.escape(a)}</p>
      </details>"""
        for q, a in faq
    )
    return f"""<section class="faq alt" aria-labelledby="faq-heading">
    <div class="container container-narrow">
      <p class="overline">FAQ</p>
      <h2 id="faq-heading" class="mb-3">{heading}</h2>
{items}
    </div>
  </section>"""


def cta_html(heading, text):
    if SITE["phone_e164"]:
        alt = f'or call <a href="tel:{SITE["phone_e164"]}" style="color: #fff; font-weight: 800;">{SITE["phone_display"]}</a>'
    else:
        alt = f'or email <a href="mailto:{SITE["email"]}" style="color: #fff; font-weight: 800;">{SITE["email"]}</a>'
    return f"""<section class="cta-band" aria-labelledby="final-cta-heading">
    <div class="container container-narrow">
      <h2 id="final-cta-heading">{heading}</h2>
      <p>{text}</p>
      <a href="#quote" class="btn btn-primary">Get a Free Quote</a>
      <p style="margin-top: 1.5rem;">{alt}</p>
    </div>
  </section>"""


def footer():
    loft = [s for s in SERVICES if s[0] not in ("loft-bathroom-conversion", "loft-kitchen-conversion", "basement-conversion", "loft-conversion-roof-terrace")]
    more = [s for s in SERVICES if s not in loft]
    loft_links = "\n".join(f'          <li><a href="/services/{slug}">{short}</a></li>' for slug, _, short in loft)
    more_links = "\n".join(f'          <li><a href="/services/{slug}">{short}</a></li>' for slug, _, short in more)
    phone = f'<a href="tel:{SITE["phone_e164"]}">{SITE["phone_display"]}</a><br>\n          ' if SITE["phone_e164"] else ""
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <a href="/" class="logo">Loft Conversions <span>London</span></a>
        <p>Dormer, hip-to-gable, mansard and Velux loft conversions across London.</p>
        <address style="font-style: normal; margin-top: 1rem;">
          {SITE["name"]}<br>
          Serving all 32 London boroughs<br>
          {phone}<a href="mailto:{SITE["email"]}">{SITE["email"]}</a>
        </address>
      </div>
      <div>
        <h4>Loft Conversions</h4>
        <ul>
{loft_links}
        </ul>
      </div>
      <div>
        <h4>More Services</h4>
        <ul>
{more_links}
          <li><a href="/about">About</a></li>
          <li><a href="/contact">Contact</a></li>
        </ul>
      </div>
      <div>
        <h4>Hours</h4>
        <ul>
          <li>{SITE["hours"]}</li>
          <li>Saturday and Sunday: closed</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <div>© <span id="year"></span> {SITE["name"]}. All rights reserved.</div>
      <div><a href="/privacy">Privacy</a> · <a href="/terms">Terms</a></div>
    </div>
  </div>
</footer>"""


def mobile_cta(quote_href):
    if SITE["phone_e164"]:
        first = f'<a href="tel:{SITE["phone_e164"]}" class="call">Call Now</a>'
    else:
        first = f'<a href="mailto:{SITE["email"]}" class="call">Email Us</a>'
    return f"""<div class="mobile-cta" id="mobile-cta" aria-hidden="true">
  {first}
  <a href="{quote_href}" class="quote">Free Quote</a>
</div>"""


# ---------------------------------------------------------------------------
# Structured data
# ---------------------------------------------------------------------------
def business_schema():
    biz = {
        "@type": "GeneralContractor",
        "@id": base_url() + "/#business",
        "name": SITE["name"],
        "description": "Loft conversions in London, including dormer, hip-to-gable, mansard, Velux, L-shaped and loft pod conversions, plus loft bathrooms, loft kitchens and basement conversions.",
        "url": base_url() + "/",
        "email": SITE["email"],
        "areaServed": {"@type": "City", "name": "London"},
        "openingHoursSpecification": [
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "opens": "08:00",
                "closes": "18:00",
            }
        ],
    }
    if SITE["phone_e164"]:
        biz["telephone"] = SITE["phone_e164"]
    return biz


def schema_graph(meta, url):
    graph = []
    if url == "/":
        graph.append(business_schema())
        graph.append({
            "@type": "WebSite",
            "@id": base_url() + "/#website",
            "url": base_url() + "/",
            "name": SITE["name"],
            "publisher": {"@id": base_url() + "/#business"},
        })
    if meta.get("breadcrumbs"):
        items = []
        for i, (name, link) in enumerate(meta["breadcrumbs"], 1):
            item = {"@type": "ListItem", "position": i, "name": html.unescape(name)}
            if link:
                item["item"] = base_url() + link
            items.append(item)
        graph.append({"@type": "BreadcrumbList", "itemListElement": items})
    svc = meta.get("service")
    if svc:
        graph.append({
            "@type": "Service",
            "name": svc["name"],
            "serviceType": svc["type"],
            "description": svc["description"],
            "provider": {"@id": base_url() + "/#business"},
            "areaServed": {"@type": "City", "name": svc.get("area", "London")},
            "url": base_url() + url,
            "offers": {"@type": "Offer", "priceCurrency": "GBP", "url": base_url() + url},
        })
    if meta.get("faq"):
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in meta["faq"]
            ],
        })
    if not graph:
        return ""
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2, ensure_ascii=False)
    return f'\n  <script type="application/ld+json">\n{data}\n  </script>'


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------
def area_links(links):
    return "\n".join(f'        <li><a href="{u}">{html.escape(a)}</a></li>' for u, a in links)


def locations_html(slug, locations):
    """The 'areas we cover' section on a service page; empty until that service has location pages."""
    links = locations.get(slug, [])
    if not links:
        return ""
    short = next(s_short for s, _, s_short in SERVICES if s == slug)
    return f"""<section aria-labelledby="areas-heading">
    <div class="container container-narrow">
      <p class="overline">Local pages</p>
      <h2 id="areas-heading">{short} Loft Conversions by London Borough</h2>
      <ul>
{area_links(links)}
      </ul>
    </div>
  </section>"""


def render(meta, body, url, locations):
    global _form_count
    _form_count = 0
    canonical = base_url() + ("/" if url == "/" else url)
    title = html.escape(meta["title"])
    desc = html.escape(meta["description"])

    body = re.sub(r"\{\{FORM:([^:}]+):([^}]+)\}\}", lambda m: quote_form(m.group(1), m.group(2)), body)
    body = body.replace("{{HOW_IT_WORKS}}", HOW_IT_WORKS)
    body = re.sub(r"\{\{LOCATIONS:([^}]+)\}\}", lambda m: locations_html(m.group(1), locations), body)
    if "{{SIBLINGS}}" in body:
        slug = url.split("/")[1]
        body = body.replace("{{SIBLINGS}}", area_links([l for l in locations.get(slug, []) if l[0] != url]))

    main = ""
    if meta.get("breadcrumbs"):
        main += "  " + breadcrumbs_html(meta["breadcrumbs"]) + "\n"
    main += body.strip("\n") + "\n"
    if meta.get("faq"):
        main += "\n  " + faq_html(meta["faq"], meta.get("faq_heading", "Frequently Asked Questions")) + "\n"
    if meta.get("cta", True):
        main += "\n  " + cta_html(
            meta.get("cta_heading", "Ready to Use the Space Above Your Head?"),
            meta.get("cta_text", "Book a free loft survey anywhere in London and get a fixed written quote."),
        ) + "\n"
    if _form_count == 0 and meta.get("cta", True):
        sys.exit(f"{url}: page has a 'Get a Free Quote' link but no form to jump to")

    # Pages without a form (privacy, terms) send quote buttons to the contact page form.
    quote_href = "#quote" if _form_count else "/contact#quote"
    robots = meta.get("robots", "index,follow")
    return f"""<!DOCTYPE html>
<!-- Generated by tools/build.py from content{"/index" if url == "/" else url}.html. Edit the content file, not this one. -->
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{canonical}">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{SITE["name"]}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="{base_url()}/assets/img/og.jpg">
  <meta property="og:url" content="{canonical}">
  <meta property="og:locale" content="en_GB">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{base_url()}/assets/img/og.jpg">

  <link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@800;900&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">

  <link rel="stylesheet" href="/assets/css/styles.css">

  <script async src="https://www.googletagmanager.com/gtag/js?id={SITE["ga4_id"]}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{SITE["ga4_id"]}');
  </script>{schema_graph(meta, url)}
</head>
<body>

{header(quote_href)}

<main>
{main}</main>

{footer()}

{mobile_cta(quote_href)}

<script src="/assets/js/main.js" defer></script>
</body>
</html>
"""


def read_page(path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("\n---\n", 1)
    if not text.startswith("---\n") or len(parts) != 2:
        sys.exit(f"{path}: missing front matter")
    meta = json.loads(parts[0][4:])
    return meta, parts[1]


# ---------------------------------------------------------------------------
# Checks: the rules every page must pass before it is written
# ---------------------------------------------------------------------------
def check(url, meta, out_html):
    problems = []
    if "—" in out_html:
        problems.append("contains an em dash")
    if len(meta["title"]) > 60:
        problems.append(f"title is {len(meta['title'])} chars (max 60)")
    if len(meta["description"]) > 160:
        problems.append(f"meta description is {len(meta['description'])} chars (max 160)")
    if out_html.count("<h1") != 1:
        problems.append(f"has {out_html.count('<h1')} <h1> tags")
    for q, a in meta.get("faq", []):
        if html.escape(a) not in out_html:
            problems.append(f"FAQ answer not visible on page: {q}")
    return problems


def build():
    pages = sorted(CONTENT.rglob("*.html"))
    sitemap = []
    titles = {}
    failed = False

    # Location pages live in content/<service-slug>/<area>.html and carry an "area" name.
    slugs = {s for s, _, _ in SERVICES}
    locations = {}
    for path in pages:
        rel = path.relative_to(CONTENT)
        if len(rel.parts) == 2 and rel.parts[0] in slugs:
            locations.setdefault(rel.parts[0], []).append((page_url(rel), read_page(path)[0]["area"]))

    for path in pages:
        rel = path.relative_to(CONTENT)
        url = page_url(rel)
        meta, body = read_page(path)
        out_html = render(meta, body, url, locations)
        problems = check(url, meta, out_html)
        if meta["title"] in titles:
            problems.append(f"title duplicates {titles[meta['title']]}")
        titles[meta["title"]] = url
        if problems:
            failed = True
            for p in problems:
                print(f"  {url}: {p}")
        out = OUT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(out_html, encoding="utf-8")
        if meta.get("sitemap"):
            sitemap.append((url, meta["sitemap"]))

    entries = "\n".join(
        f"""  <url>
    <loc>{base_url()}{url}</loc>
    <lastmod>{BUILD_DATE}</lastmod>
    <changefreq>{sm["changefreq"]}</changefreq>
    <priority>{sm["priority"]}</priority>
  </url>"""
        for url, sm in sitemap
    )
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n',
        encoding="utf-8",
    )
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base_url()}/sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(pages)} pages, {len(sitemap)} in sitemap.")
    if failed:
        sys.exit("Some pages failed the checks above.")


if __name__ == "__main__":
    build()
