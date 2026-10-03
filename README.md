# Peptide Calculator Pro

Static site for [peptidecalculatorpro.org](https://peptidecalculatorpro.org): free, browser-based peptide calculators with supporting copy.

| Page | Path |
|---|---|
| Peptide Calculator | `/` |
| Peptide Reconstitution Calculator | `/peptide-reconstitution-calculator/` |
| Peptide Dosage Calculator | `/peptide-dosage-calculator/` |
| Peptide Blend Calculator | `/peptide-blend-calculator/` |
| Peptide Dilution Calculator | `/peptide-dilution-calculator/` |
| Peptide Concentration Calculator | `/peptide-concentration-calculator/` |
| Retatrutide Peptide Calculator | `/retatrutide-peptide-calculator/` |
| TDEE Calculator | `/tdee-calculator/` |

## Build

```bash
python3 build.py
```

Writes the site to `dist/` (no dependencies). Page bodies live in `src/`, shared CSS/JS/images in `assets/`, and the domain is set by `SITE_URL` in `build.py`.

## Deploy

On AnySites (Node): `npm start` runs `server.js`, a zero-dependency static server for `dist/` on `$PORT` (default 3000). No build command is needed because `dist/` is committed — run `python3 build.py` locally and commit the result after editing `src/`.

Any static host also works: publish the `dist/` directory. Redirect `www` to the apex domain with a 301 and keep trailing slashes on URLs.
