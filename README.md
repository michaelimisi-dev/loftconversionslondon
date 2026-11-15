# Loft Conversions London

Static website for loftconversionslondon.co.uk, built to deploy on Cloudflare Pages.

## How the site is put together

- `content/` holds every page: a JSON block of settings (title, description, FAQs) followed by the page's HTML.
- `tools/build.py` turns `content/` into the finished website in `site/`, adding the shared header, footer, quote forms, FAQ sections, structured data, `sitemap.xml` and `robots.txt`.
- `site/` is what gets deployed. Don't edit the HTML pages in it directly, because the next build overwrites them. `site/assets/`, `site/_headers` and `site/_redirects` are edited by hand.

After any change to `content/` or `tools/build.py`, rebuild:

```bash
python tools/build.py
```

The build stops with a message if a page breaks a rule: an em dash, a title over 60 characters, a description over 160, more than one H1, or FAQ text that doesn't match its structured data.

To preview locally (pretty URLs work like they do on Cloudflare):

```bash
python tools/serve.py
```

Then open http://localhost:8080.

## Before launch

1. **Phone number.** Set `phone_e164` (e.g. `+442012345678`) and `phone_display` (e.g. `020 1234 5678`) in the `SITE` settings at the top of `tools/build.py`, then rebuild. Every page gets a tap-to-call header button, a "Call Now" mobile bar and the number in the footer and structured data. Also add it to the contact page list in `content/contact.html` (search for `PHONE PLACEHOLDER`).
2. **Google Analytics.** Replace `G-XXXXXXXXXX` with your GA4 measurement ID in `SITE` in `tools/build.py`, then rebuild.
3. **Business claims.** Search the project for `BUSINESS CLAIM`. Each marks a promise the builder renting the site must confirm (insurance, call-back time) or details to add (about page story, accreditations). Never add accreditations, reviews or numbers the builder can't prove.
4. **Social sharing image.** Add a 1200×630 image at `site/assets/img/og.jpg`.
5. **Legal pages.** `content/privacy.html` and `content/terms.html` are templates. Add the operating business's legal name and address, and have them reviewed.

## Deploy to Cloudflare Pages

The site deploys from GitHub: every push to `main` publishes the `site/` folder. It was set up in the Cloudflare dashboard under Workers & Pages → Create application → Pages → Import an existing Git repository, with framework preset None, no build command (or `exit 0`) and build output directory `site`. Run `python tools/build.py` before pushing, because Cloudflare publishes the committed files as they are.

To deploy by hand instead:

```bash
npx wrangler pages deploy ./site --project-name=loftconversionslondon
```

### Domain

1. Add `loftconversionslondon.co.uk` to Cloudflare (Add a domain, Free plan). Before changing nameservers, check that the imported DNS records include the domain's MX and email records, or email to info@loftconversionslondon.co.uk will stop, and so will the leads.
2. At the domain registrar, replace the nameservers with the two Cloudflare gives you, and wait for the domain to show as Active.
3. In Workers & Pages → loftconversionslondon → Custom domains, add `loftconversionslondon.co.uk`, then `www.loftconversionslondon.co.uk`.
4. Redirect www to the main domain with a Redirect Rule (Rules → Redirect Rules → the "Redirect from WWW to root" template). Pages does not do this on its own.
5. Under SSL/TLS → Edge Certificates, turn on Always Use HTTPS.

## Lead forms (FormSubmit)

Forms post to `https://formsubmit.co/ajax/info@loftconversionslondon.co.uk`. No backend is needed.

- **Activate first.** The first submission sends an "Activate" email to info@loftconversionslondon.co.uk. Click the link in it, or no leads will arrive. Submit a test lead straight after deploying.
- **Reply-to.** The forms don't ask for an email address (fewer fields means more enquiries), so replies go by phone. If you add an `email` field, FormSubmit sets it as the reply-to address automatically.
- **CC.** No CC address is set. If you add a `_cc` hidden field, note that FormSubmit only supports CC, not BCC, so the lead recipient will see that address.
- **Hide the address (optional).** After activation, FormSubmit gives you a hashed token. Replace the email address in the form action in `tools/build.py` with the token, so spammers can't harvest it from the page source.

## After launch

1. Add the domain to Google Search Console and submit `https://loftconversionslondon.co.uk/sitemap.xml`.
2. Create or link a Google Business Profile (service-area business, no public address).
3. Test the homepage and one service page in Google's Rich Results Test.
4. Run PageSpeed Insights on mobile and desktop.
