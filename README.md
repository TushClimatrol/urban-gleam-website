# Urban Gleam website

Live at <https://urbangleamcleaning.com>. Pushing to `main` deploys automatically (Render static site, publish directory `.`).

## How the site is put together

| What | Where | Edit by hand? |
|---|---|---|
| Homepage, booking form, all CSS and JavaScript | `index.html` | Yes |
| Prices, extras, what each service includes | the `CONFIG` block and `SERVICE_PAGES` inside the `<script>` in `index.html` | Yes |
| Areas and their local details | `tools/areas.json` | Yes |
| Photos, alt text, which photo shows where | `tools/photos.json` + files in `img/` | Yes |
| Page titles and search descriptions | `HOME` / `SERVICE_META` at the top of `tools/build-seo.py` | Yes |
| `services/`, `areas/`, `privacy/`, `legal/`, `404.html`, old-address redirects (`about-us/`, `prices/` …), `assets/site.css`, `sitemap.xml`, `robots.txt` | generated | **No** — they are rewritten on every build |

## After any change

```
python3 tools/build-seo.py
```

Needs Python 3 and Node. It rebuilds every generated page from `index.html` and the two JSON files, and prints a
"CHECK THESE" list if a title or description is duplicated or too long. Run it, review, commit everything, push.

After adding or swapping a photo, run this first (needs `pip install Pillow`):

```
python3 tools/optimise-images.py
```

## Things worth knowing

- **Opening hours** appear in `index.html` (`OPEN_HOUR` / `CLOSE_HOUR`, the contact card, the footer) and in `BIZ`
  in `tools/build-seo.py`. Change all of them together, and keep the Google Business Profile the same.
- **The `<!-- name:start -->…<!-- name:end -->` markers** in `index.html` are filled in by the build. Don't remove them.
- **`google-site-verification`** in the `<head>` of `index.html` proves ownership to Google Search Console. Don't remove it.
- **Addresses.** Render answers unknown addresses with `index.html`; the small script at the top of its `<head>` then
  sends `/areas/kingston` to `/areas/kingston/`, sends old-site addresses to their new home, and marks anything else
  "noindex" so Google never files a copy of the homepage under a made-up address.
- **`tools/lastmod.json`** remembers when each page last really changed, so the sitemap dates stay truthful. Commit it.
- **Area pages** must stay specific to their area. If you add one, give it real local detail in `tools/areas.json`;
  pages that only swap the town name are what Google's spam policy calls doorway pages.
