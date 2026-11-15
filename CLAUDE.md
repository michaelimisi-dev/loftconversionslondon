# Loft Conversions London

Rank-and-rent lead-generation website for loftconversionslondon.co.uk, built with the `local-design` skill. The owner (GitHub: michaelimisi-dev) does not run a building firm yet; the site will be rented to a London loft builder.

## Where things stand (as of 15 November 2026)

- 49 pages built and live at https://loftconversionslondon.michaelimisi25.workers.dev (homepage, 12 service pages, about, contact, privacy, terms, 32 location pages).
- Hosted as a Cloudflare Worker with static assets, connected to GitHub `michaelimisi-dev/loftconversionslondon`. Every push to `main` redeploys automatically using `wrangler.jsonc`, which points at `site/`.
- All work is committed and pushed.

## Next steps

1. Connect the domain: add loftconversionslondon.co.uk to Cloudflare (keep the MX/email records), switch nameservers at the registrar, add the domain and www in Workers & Pages → loftconversionslondon → Settings → Domains & Routes.
2. Add the www → root Redirect Rule and turn on Always Use HTTPS. Then recheck the live site on the real domain, including the Strict-Transport-Security header, which did not show on workers.dev.
3. Activate FormSubmit: submit one test lead, then click Activate in the email to info@loftconversionslondon.co.uk.
4. Local-design skill step 7 (IndexChex Google indexing): only after the domain is live, and only with the owner's own IndexChex API key. Submit the homepage, service pages and location pages, not about/contact/legal.
5. When available: phone number and GA4 ID go in `SITE` in `tools/build.py`; confirm every `BUSINESS CLAIM` comment with the builder who rents the site.

## How the site works

- Edit pages in `content/` (JSON front matter, then HTML), never the generated HTML in `site/`. Shared header, footer, forms, FAQs and schema come from `tools/build.py`.
- After any change: `python tools/build.py`, then `python tools/check_site.py`, then commit and push. Cloudflare publishes the committed `site/` files as they are.
- Preview locally with `python tools/serve.py` (port 8080; `.claude/launch.json` has a "site" config).
- Location pages: `content/<service-slug>/<borough>.html` with an `"area"` key; service pages list them automatically via `{{LOCATIONS:slug}}`, and siblings via `{{SIBLINGS}}`.

## Decisions to keep

- No em dashes anywhere in copy (the build enforces this).
- No fake reviews, ratings, project counts or accreditations (TrustMark, FMB, etc.). A "How it works" section stands in for reviews. UK law bans fake reviews.
- Every statistic is sourced, with a numbered sources list on each page. Location pages are grounded in each council's own planning guidance; say so honestly where a council is likely to refuse something.
- No phone number yet: the quote form is the main call to action; mobile bar shows "Email Us" + "Free Quote".
- Forms post to FormSubmit with no CC address. Fields: name, phone, type of conversion, postcode.
- Colours: charcoal #484D4E, light grey #DFDFE0, orange #FF6900 buttons with dark text (#1A1A1A), #B84E00 for orange text on light backgrounds. Fonts: Montserrat 800/900 and Inter.
- The `local-design` skill was installed from a zip with two things removed: a third-party default CC email and a hardcoded IndexChex API key. Never reintroduce either.
