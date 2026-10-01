# Peptide Calculator Pro

Static site for [peptidecalculatorpro.org](https://peptidecalculatorpro.org): three free, browser-based peptide calculators with supporting copy.

| Page | Path |
|---|---|
| Peptide Calculator | `/` |
| Peptide Reconstitution Calculator | `/peptide-reconstitution-calculator/` |
| Peptide Dosage Calculator | `/peptide-dosage-calculator/` |

## Build

```bash
python3 build.py
```

Writes the site to `dist/` (no dependencies). Page bodies live in `src/`, shared CSS/JS/images in `assets/`, and the domain is set by `SITE_URL` in `build.py`.

## Deploy

Publish the `dist/` directory to any static host (Cloudflare Pages, Netlify, Vercel). Redirect `www` to the apex domain with a 301 and keep trailing slashes on URLs.
