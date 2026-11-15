"""Check the built site in site/ after running tools/build.py.

Reports broken internal links, invalid structured data, leftover {{placeholders}},
location pages under the 500-word minimum, and location pages that share long
passages of identical text (more than 25% of their 8-word phrases).

Run:  python tools/check_site.py
"""

import itertools
import json
import pathlib
import re
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
MIN_LOCATION_WORDS = 500


def url_of(path):
    rel = path.relative_to(SITE).as_posix()[: -len(".html")]
    return "/" if rel == "index" else "/" + rel


def unique_words(text):
    """Words in <main>, minus the shared form, closing call to action and source list."""
    main = text.split("<main>")[1].split("</main>")[0].split('class="sources"')[0]
    main = re.sub(r'<form.*?</form>|<section class="cta-band".*?</section>', "", main, flags=re.S)
    return re.sub(r"<[^>]+>", " ", main).split()


def phrases(words, n=8):
    return {" ".join(words[i : i + n]) for i in range(len(words) - n)}


def main():
    pages = sorted(SITE.rglob("*.html"))
    urls = {url_of(p) for p in pages}
    problems = []
    locations = {}

    for p in pages:
        text = p.read_text(encoding="utf-8")
        url = url_of(p)
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            try:
                json.loads(block)
            except json.JSONDecodeError as e:
                problems.append(f"{url}: invalid JSON-LD ({e})")
        if "{{" in text:
            problems.append(f"{url}: unreplaced placeholder")
        ids = set(re.findall(r'id="([^"]+)"', text))
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http", "mailto:", "tel:")):
                continue
            path, _, frag = href.partition("#")
            if not path and frag and frag not in ids:
                problems.append(f"{url}: link to missing #{frag}")
            elif path and path not in urls and not path.startswith("/assets"):
                problems.append(f"{url}: broken link {href}")
        if len(p.relative_to(SITE).parts) == 2 and p.parent.name.endswith("conversion") and p.parent.name != "services":
            words = unique_words(text)
            locations[url] = words
            if len(words) < MIN_LOCATION_WORDS:
                problems.append(f"{url}: {len(words)} unique words (min {MIN_LOCATION_WORDS})")

    grams = {u: phrases(w) for u, w in locations.items()}
    for a, b in itertools.combinations(sorted(grams), 2):
        overlap = len(grams[a] & grams[b]) / max(1, min(len(grams[a]), len(grams[b])))
        if overlap > 0.25:
            problems.append(f"{a} and {b} share {overlap:.0%} of their phrasing")

    print(f"Checked {len(pages)} pages, {len(locations)} location pages.")
    for p in problems:
        print("  " + p)
    if problems:
        sys.exit("Problems found.")
    print("No problems found.")


if __name__ == "__main__":
    main()
