# PassPlay site

[![Static site validation](https://github.com/Nathan-Gomes/passplay-site/actions/workflows/validate.yml/badge.svg)](https://github.com/Nathan-Gomes/passplay-site/actions/workflows/validate.yml)

Public pages for the PassPlay iOS app:
- `index.html` — Support & Help
- `privacy.html` — Privacy Policy

Served via GitHub Pages.

## Validate locally

Run the dependency-free site check before publishing:

```bash
python3 scripts/check_site.py
```

The check verifies page metadata, accessibility landmarks, skip links, unique element IDs,
and local links, including same-page and cross-page fragments.
