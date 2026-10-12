#!/usr/bin/env python3
"""Urban Gleam site build.

Run from the repo root after editing index.html, tools/areas.json or tools/photos.json:

    python3 tools/build-seo.py

Needs Python 3 and Node (Node only reads the price/service data out of index.html).
Safe to run again and again: every step rewrites its own output from scratch.

What it does
  1. index.html   title, description, canonical/social tags, structured data, the address check in
                  <head>, the photo gallery markup, area links and footer service links.
  2. assets/site.css            the homepage CSS plus the styles for the generated pages.
  3. services/                  the services & prices hub and one page per service (text, prices and
                                FAQs come from SERVICES / SERVICE_PAGES inside index.html).
  4. areas/                     the areas index and one page per area in tools/areas.json.
  5. privacy/ legal/            the policy pages, from STATIC_PAGES inside index.html.
  6. 404.html + old-address redirects (about-us/, prices/, ...) left over from the previous website.
  7. sitemap.xml + robots.txt   lastmod only changes when a page's content really changes
                                (tracked in tools/lastmod.json).

Where to change things
  * Prices, extras, what each service includes ....... the CONFIG block at the top of the <script> in index.html
  * Page titles and search descriptions ............... HOME / SERVICE_META below (areas: built from areas.json)
  * Areas and their local details ..................... tools/areas.json
  * Photos, alt text, which photo shows on which page . tools/photos.json (then run tools/optimise-images.py)
  * Opening hours ..................................... BIZ below AND the visible text in index.html
                                                        (OPEN_HOUR/CLOSE_HOUR, contact card, footer)
"""
import hashlib, html, json, os, re, shutil, subprocess, sys
from datetime import date
from math import asin, cos, radians, sin, sqrt
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# ====================================================================== configuration
SITE = 'https://urbangleamcleaning.com'
BIZ = {
    'name': 'Urban Gleam Ltd',
    'short': 'Urban Gleam',
    'phone_display': '07942 369735',
    'phone_e164': '+447942369735',
    'whatsapp': '447942369735',
    'email': 'contact@urbangleamcleaning.com',
    'street': 'Braemar House, Kings Avenue',
    'town': 'Sunbury-on-Thames',
    'county': 'Surrey',
    'postcode': 'TW16 7QE',
    'lat': 51.4268394, 'lng': -0.4221821,
    'gbp': 'https://maps.google.com/?cid=10111168519048199372',
    'opens': '07:00', 'closes': '20:00', 'hours_text': '7am–8pm',
    # real profile URLs only (Facebook page, Instagram account ...) — they are added to the structured data
    'social': [],
}
HOME = {
    'title': 'Urban Gleam | Eco-Friendly Cleaners in London & Surrey',
    'desc': 'Vetted, insured eco-friendly cleaners for homes and offices across London & Surrey. Domestic cleaning from £22.50/hr, end of tenancy from £130. Book online.',
}
# slug, id used inside index.html, <title>, search description
SERVICE_META = [
    ('domestic-cleaning', 'domestic', 'Domestic Cleaning in London & Surrey from £22.50/hr',
     'Regular weekly or fortnightly home cleaning by the same vetted, insured cleaner. Eco-friendly products included, from £22.50/hr across London & Surrey.'),
    ('office-cleaning', 'office', 'Office Cleaning in London & Surrey from £25/hr',
     'Office cleaning across London & Surrey — daily, weekly or out of hours. Vetted, insured cleaners and low-odour eco products, from £25/hr.'),
    ('end-of-tenancy-cleaning', 'eot', 'End of Tenancy Cleaning in London & Surrey from £130',
     'End of tenancy cleaning to letting-agent checklist standard. Fixed prices from £130 by property size, carpets optional. London & Surrey, 7 days a week.'),
    ('after-builders-cleaning', 'builders', 'After Builders Cleaning in London & Surrey from £130',
     'After builders cleaning that removes fine dust, paint splashes and debris with HEPA vacuums. Fixed prices from £130 by property size. London & Surrey.'),
    ('spring-cleaning', 'spring', 'Spring Cleaning & Deep Cleaning in London & Surrey',
     'A full spring or deep clean — inside cupboards, behind appliances, tiles, grout and limescale. Eco-friendly products, from £25/hr (minimum 4 hours).'),
    ('one-off-cleaning', 'oneoff', 'One-Off Deep Cleaning in London & Surrey from £25/hr',
     'A single deep clean with no ongoing commitment — before guests, after a busy stretch or for an inspection. From £25/hr, minimum 4 hours. Book online.'),
    ('after-party-cleaning', 'party', 'After Party Cleaning in London & Surrey from £25/hr',
     'Fast, discreet after party cleaning — rubbish, glassware, spills, kitchen and bathrooms reset. From £25/hr, 7 days a week across London & Surrey.'),
    ('emergency-cleaning', 'emergency', 'Emergency & Same-Day Cleaning in London & Surrey',
     'Urgent same-day cleaning across London & Surrey for spills, inspections and last-minute viewings. From £30/hr, £120 minimum. Call 07942 369735.'),
]
SLUG_BY_ID = {sid: slug for slug, sid, _, _ in SERVICE_META}
SHORT_NAME = {'domestic': 'Domestic cleaning', 'office': 'Office cleaning', 'eot': 'End of tenancy cleaning',
              'builders': 'After builders cleaning', 'spring': 'Spring cleaning', 'oneoff': 'One-off deep cleaning',
              'party': 'After party cleaning', 'emergency': 'Emergency cleaning'}
# one line per service for the hub page and "which clean do I need?"
HUB_LINE = {
    'domestic': 'Weekly, fortnightly or monthly cleans by the same trusted cleaner.',
    'office': 'Daily, weekly or out-of-hours cleaning for workplaces.',
    'eot': 'A checklist-driven deep clean of the whole property when you move out.',
    'builders': 'Fine dust, paint splashes and debris removed after building work.',
    'spring': 'Our most thorough seasonal clean, into every cupboard and corner.',
    'oneoff': 'One intensive visit with no ongoing commitment, built around your priorities.',
    'party': 'The morning-after reset: rubbish, glassware, floors, kitchen and bathrooms.',
    'emergency': 'A priority same-day clean when it can’t wait.',
}
# the other names people search for, said once in plain English on each service page
ALSO_KNOWN_AS = {
    'domestic': 'You might know it as house cleaning, home cleaning or simply having a regular cleaner — it’s all the same service.',
    'office': 'Some people call it commercial or workplace cleaning; either way, it’s built around your opening hours.',
    'eot': 'You may also see it called a move-out clean, a check-out clean or end of lease cleaning.',
    'builders': 'It’s also known as post-construction, post-renovation or builders’ cleaning.',
    'spring': 'If you’re looking for a “deep clean” of the whole home, this is it.',
    'oneoff': 'Some people call it a one-time clean or a one-off deep clean.',
    'party': 'It’s also booked as post-party or after-event cleaning.',
    'emergency': 'People also ask for same-day, urgent or last-minute cleaning — this is that service.',
}
HOW_BOOKING_WORKS = [
    ('Choose your service', 'Tell us the size of the job: hours for hourly services, bedrooms for fixed-price cleans.'),
    ('Pick a date and time', 'Slots are available seven days a week.'),
    ('Add your details', 'Your address, how we get in, and any notes — pets, parking, focus areas.'),
    ('Confirm', 'Your booking comes straight to us and we confirm your slot by phone or email. You pay after the clean.'),
]
WHICH_CLEAN = [
    ('You’re moving out of a rented home', 'eot'),
    ('You want the house kept clean every week or fortnight', 'domestic'),
    ('The builders have just left', 'builders'),
    ('You want one top-to-bottom reset, with no commitment', 'oneoff'),
    ('It’s time for the big once-a-year clean', 'spring'),
    ('You need a workplace cleaned', 'office'),
    ('You hosted last night', 'party'),
    ('It has to be done today', 'emergency'),
]
# addresses from the previous website that other sites and Google may still point at -> where they go now
MOVED = {
    '/about-us': '/', '/prices': '/services/#prices', '/book-online': '/#book', '/contact-us': '/#contact',
    '/testimonials': '/#reviews', '/blog': '/', '/privacy-policy': '/privacy/', '/legal-notice': '/legal/',
}
HOME_AREA = 'sunbury-on-thames'        # the area page for the town the office is in
TODAY = date.today().isoformat()

AREA_DATA = json.load(open('tools/areas.json', encoding='utf-8'))
AREAS = AREA_DATA['areas']
GROUPS = AREA_DATA['groups']
PHOTOS = json.load(open('tools/photos.json', encoding='utf-8'))
GALLERY = PHOTOS['gallery']
PHOTO_BY_FILE = {p['file']: p for p in GALLERY}
CARD = PHOTOS['brand']['card']
CROPS = PHOTOS['brand']['crops']

# ====================================================================== helpers
def esc(s): return html.escape(s, quote=True)
def strip_tags(s): return re.sub(r'<[^>]+>', '', s)
def amp(s):
    """Escape bare ampersands in text that may already contain HTML tags/entities."""
    return re.sub(r'&(?!(?:[a-zA-Z][a-zA-Z0-9]*|#[0-9]+|#x[0-9a-fA-F]+);)', '&amp;', s)
def read(p): return open(p, encoding='utf-8').read()
def write(p, s):
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)
def money(v):
    return '£' + (f'{v:.2f}' if abs(v - round(v)) > 1e-9 else f'{v:.0f}')
def join_and(items):
    items = list(items)
    return items[0] if len(items) == 1 else ', '.join(items[:-1]) + ' and ' + items[-1]
def miles_from_base(a):
    la1, lo1, la2, lo2 = map(radians, (BIZ['lat'], BIZ['lng'], a['lat'], a['lng']))
    d = 2 * asin(sqrt(sin((la2 - la1) / 2) ** 2 + cos(la1) * cos(la2) * sin((lo2 - lo1) / 2) ** 2)) * 3958.8
    return d * 1.25          # straight line -> rough road distance
def distance_phrase(a):
    m = miles_from_base(a)
    if m < 1.5: return 'under two miles'
    return f'about {round(m)} miles'
def near_base(a):
    """Only quote the distance where being close is the point (roughly Egham / Kingston / Richmond and nearer)."""
    return round(miles_from_base(a)) <= 7
def fill(s): return s.replace('{hours}', BIZ['hours_text'])
def replace_block(text, name, content):
    """Swap whatever sits between <!-- name:start --> and <!-- name:end -->."""
    pat = re.compile(r'<!-- ' + re.escape(name) + r':start -->.*?<!-- ' + re.escape(name) + r':end -->', re.S)
    if not pat.search(text):
        sys.exit(f'index.html: marker "{name}" not found')
    return pat.sub(lambda m: f'<!-- {name}:start -->{content}<!-- {name}:end -->', text, count=1)

def picture(p, sizes, extra=''):
    """<picture> with WebP sources and the original JPEG as the fallback Google Images indexes."""
    webp = ', '.join(f"/img/{v['file']} {v['w']}w" for v in p.get('webp', []))
    src = f'<source type="image/webp" srcset="{webp}" sizes="{sizes}">' if webp else ''
    return (f'<picture>{src}<img src="/img/{p["file"]}" alt="{esc(p["alt"])}" width="{p["w"]}" height="{p["h"]}" '
            f'loading="lazy" decoding="async"{extra}></picture>')

# ====================================================================== 1. read index.html and its data
h = read('index.html')

# (legacy) photos pasted into index.html as base64 are moved out to /img
_n = [len(GALLERY)]
def _extract(m):
    import base64
    _n[0] += 1
    ext = 'jpg' if m.group(1) in ('jpeg', 'jpg') else m.group(1)
    fn = f'img/photo-{_n[0]:02d}.{ext}'
    open(fn, 'wb').write(base64.b64decode(m.group(2)))
    print('  extracted embedded image ->', fn, '(add it to tools/photos.json)')
    return '/' + fn
h = re.sub(r'data:image/(\w+);base64,([A-Za-z0-9+/=]{100,})', _extract, h)

def js_const(name):
    """Evaluate `const NAME = {...};` from the page script with Node and return it as Python data."""
    m = re.search(r'\n  const ' + name + r' = ', h)
    if not m: sys.exit(f'index.html: const {name} not found')
    s = m.end()
    close = {'{': '}', '[': ']'}[h[s]]
    eol = h.index('\n', s)
    e = eol - 1 if h[eol - 2:eol] == close + ';' else h.index('\n  ' + close + ';', s) + 4
    return json.loads(subprocess.check_output(['node', '-e', f'console.log(JSON.stringify({h[s:e]}))']).decode())

SERVICES = js_const('SERVICES')          # rates, minimums
EOT_PRICES = js_const('EOT_PRICES')      # fixed prices by property size [without carpets, with carpets]
EOT_PRICES = dict(sorted(EOT_PRICES.items(), key=lambda kv: (kv[0] != 'studio', kv[0])))    # studio first, then 1, 2, 3, 4+
EOT_LABELS = js_const('EOT_LABELS')
SP = js_const('SERVICE_PAGES')           # copy for each service page
STATIC = js_const('STATIC_PAGES')        # privacy / legal copy
for _, sid, _, _ in SERVICE_META:
    assert sid in SERVICES and sid in SP, f'service {sid} missing from index.html'

def is_fixed(sid): return bool(SERVICES[sid].get('fixed'))
FIXED_FROM = min(v[0] for v in EOT_PRICES.values() if v)
def price_line(sid):
    return f'fixed from {money(FIXED_FROM)}' if is_fixed(sid) else f'from {money(SERVICES[sid]["rate"])}/hr'
def min_line(sid):
    s = SERVICES[sid]
    if is_fixed(sid): return 'Priced by property size'
    return f'Minimum {s["minH"]} hours · {money(s["min"])}' if s['minH'] > 2 else f'Minimum {money(s["min"])} per visit'

HOME_FAQ = re.findall(r'<button class="faq-q"[^>]*>(.*?)<span class="faq-icon">.*?<div class="faq-a"><p>(.*?)</p>',
                      h[h.index('id="faq"'):h.index('id="contact"')], flags=re.S)
# testimonials on the homepage: (quote, name, tag line)
REVIEWS = [(strip_tags(q).strip().strip('"“”'), w.strip(), t.strip()) for q, w, t in re.findall(
    r'<blockquote>(.*?)</blockquote><div class="who">(.*?)</div><div class="tag">(.*?)</div>', h, flags=re.S)]
REVIEW_SERVICE = [('end of tenancy', ['eot']), ('office', ['office']), ('deep', ['spring', 'oneoff']),
                  ('home cleaning', ['domestic']), ('domestic', ['domestic']), ('builders', ['builders'])]
def reviews_for_service(sid):
    return [r for r in REVIEWS if any(k in r[2].lower() and sid in ids for k, ids in REVIEW_SERVICE)]
def review_for_area(a):
    for r in REVIEWS:
        parts = [x.strip().lower() for x in r[2].split('·')]
        if any(a['name'].lower() in x or x == a['short'].lower() for x in parts): return r
    return None
def quote_card(r):
    return (f'<figure class="quote-card"><div class="stars" aria-hidden="true">★★★★★</div>'
            f'<blockquote>“{esc(r[0])}”</blockquote><figcaption><strong>{esc(r[1])}</strong> · {amp(r[2])}</figcaption></figure>')

# ====================================================================== 2. structured data
def postal():
    return {"@type": "PostalAddress", "streetAddress": BIZ['street'], "addressLocality": BIZ['town'],
            "addressRegion": BIZ['county'], "postalCode": BIZ['postcode'], "addressCountry": "GB"}
BIZ_IMAGES = [f"{SITE}/img/{CROPS[k]['file']}" for k in ('1x1', '4x3', '16x9')]

def ld_business_full():
    return {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "@id": SITE + "/#business",
        "name": BIZ['name'],
        "alternateName": ["Urban Gleam", "Urban Gleam Cleaning"],
        "description": "Eco-friendly domestic, office, end of tenancy and after-builders cleaning across London, Surrey and the M25, based in Sunbury-on-Thames.",
        "url": SITE + "/",
        "telephone": BIZ['phone_e164'],
        "email": BIZ['email'],
        "image": BIZ_IMAGES,
        "logo": SITE + "/favicon-512.png",
        "priceRange": "££",
        "currenciesAccepted": "GBP",
        "paymentAccepted": "Cash, Credit Card, Debit Card, Bank Transfer, PayPal",
        "address": postal(),
        "geo": {"@type": "GeoCoordinates", "latitude": BIZ['lat'], "longitude": BIZ['lng']},
        "hasMap": BIZ['gbp'],
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "opens": BIZ['opens'], "closes": BIZ['closes']}],
        "areaServed": [{"@type": "AdministrativeArea", "name": "Greater London"}, {"@type": "AdministrativeArea", "name": "Surrey"}]
                      + [{"@type": "Place", "name": a['name']} for a in AREAS.values()],
        "sameAs": [BIZ['gbp']] + BIZ['social'],
        "knowsAbout": ["Domestic cleaning", "Office cleaning", "End of tenancy cleaning", "After builders cleaning", "Deep cleaning", "Eco-friendly cleaning"],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Cleaning services", "itemListElement": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": SHORT_NAME[sid], "url": f"{SITE}/services/{slug}/"}}
            for slug, sid, _, _ in SERVICE_META]},
    }
def biz_ref():
    """The business, briefly, for pages other than the homepage (same @id as the full record)."""
    return {"@type": "LocalBusiness", "@id": SITE + "/#business", "name": BIZ['name'], "url": SITE + "/",
            "telephone": BIZ['phone_e164'], "image": BIZ_IMAGES[2], "priceRange": "££", "address": postal()}
def ld_faq(items):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": strip_tags(q).strip(), "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a).strip()}}
        for q, a in items]}
def ld_script(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'
def ld_offer(sid):
    if is_fixed(sid):
        spec = {"@type": "PriceSpecification", "priceCurrency": "GBP", "minPrice": f"{FIXED_FROM:.2f}"}
    else:
        spec = {"@type": "UnitPriceSpecification", "priceCurrency": "GBP", "price": f"{SERVICES[sid]['rate']:.2f}", "unitCode": "HUR", "unitText": "hour"}
    return {"@type": "Offer", "priceCurrency": "GBP", "url": f"{SITE}/#book", "priceSpecification": spec}

def seo_head(url, title, desc, ld=(), image=None, image_alt=None, robots='index, follow, max-image-preview:large'):
    image = image or (f"{SITE}/img/{CARD['file']}", CARD['w'], CARD['h'])
    image_alt = image_alt or CARD['alt']
    lines = []
    if url:
        lines.append(f'<link rel="canonical" href="{url}">')
    lines.append(f'<meta name="robots" content="{robots}">')
    lines += [
        '<meta name="geo.region" content="GB-SRY"><meta name="geo.placename" content="Sunbury-on-Thames">',
        f'<meta name="geo.position" content="{BIZ["lat"]};{BIZ["lng"]}"><meta name="ICBM" content="{BIZ["lat"]}, {BIZ["lng"]}">',
        '<meta property="og:type" content="website"><meta property="og:site_name" content="Urban Gleam"><meta property="og:locale" content="en_GB">',
    ]
    if url:
        lines.append(f'<meta property="og:url" content="{url}">')
    lines += [
        f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:image" content="{image[0]}"><meta property="og:image:width" content="{image[1]}"><meta property="og:image:height" content="{image[2]}"><meta property="og:image:alt" content="{esc(image_alt)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{image[0]}">',
    ]
    return '\n'.join(lines + [ld_script(o) for o in ld])

# ====================================================================== 3. index.html
h = re.sub(r'<title>.*?</title>', lambda m: f'<title>{esc(HOME["title"])}</title>', h, count=1)
h = re.sub(r'<meta name="description" content="[^"]*">', lambda m: f'<meta name="description" content="{esc(HOME["desc"])}">', h, count=1)

home_ld = [ld_business_full(),
           {"@context": "https://schema.org", "@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "Urban Gleam",
            "alternateName": ["Urban Gleam Cleaning", "Urban Gleam Ltd", "urbangleamcleaning.com"],
            "publisher": {"@id": SITE + "/#business"}, "inLanguage": "en-GB"},
           ld_faq(HOME_FAQ)]
h = replace_block(h, 'seo', '\n' + seo_head(SITE + '/', HOME['title'], HOME['desc'], home_ld) + '\n')

# every real page, for the address check below (index.html is also what the host serves for unknown addresses)
PAGE_PATHS = (['/services/'] + [f'/services/{slug}/' for slug, _, _, _ in SERVICE_META] +
              ['/areas/'] + [f'/areas/{s}/' for s in AREAS] + ['/privacy/', '/legal/'])
def guard_js(not_found_flag):
    """Runs before anything else. The host answers unknown addresses with this page, so:
       /areas/kingston -> /areas/kingston/ ; old-site addresses -> their new home ; anything else is
       flagged so search engines don't index a copy of the homepage under a made-up address."""
    tail = ("var m=document.createElement('meta');m.name='robots';m.content='noindex';document.head.appendChild(m);window.__ugNotFound=1;"
            if not_found_flag else '')
    return ('<script>(function(){var p=location.pathname;if(p==="/"||p==="/index.html")return;'
            'var K=' + json.dumps(PAGE_PATHS, separators=(',', ':')) + ',M=' + json.dumps(MOVED, separators=(',', ':')) + ';'
            'var b=p.replace(/\\/index\\.html$/,"").replace(/\\/+$/,"").toLowerCase();'
            'var t=K.indexOf(b+"/")>-1?(b+"/"===p?"":b+"/"+location.search+location.hash):M[b];'
            'if(t){location.replace(t);return;}' + tail + '})();</script>')
h = replace_block(h, 'route-guard', guard_js(True))

# gallery: plain HTML slides so photos, alt text and captions are in the page itself
NO_DRAG = ' draggable="false"'
slides = ''.join(
    f'<figure class="gal-slide">{picture(p, "(max-width: 1020px) 92vw, 940px", NO_DRAG)}'
    f'<figcaption class="gal-cap"><span class="c-text">{esc(p["caption"])}</span><span class="c-tag">{esc(p["tag"])}</span></figcaption></figure>'
    for p in GALLERY)
h = replace_block(h, 'gallery', slides)
h = re.sub(r'(<span class="gal-count" id="gal-count">)[^<]*(</span>)', lambda m: f'{m.group(1)}1 / {len(GALLERY)}{m.group(2)}', h, count=1)

# service links
for slug, sid, _, _ in SERVICE_META:
    h = h.replace(f'href="#/service/{sid}"', f'href="/services/{slug}/"')
foot_services = '\n'.join(f'          <li><a href="/services/{slug}/">{SHORT_NAME[sid]}</a></li>' for slug, sid, _, _ in SERVICE_META)
foot_services += '\n          <li><a href="/services/">All services &amp; prices</a></li>'
h, n_ = re.subn(r'(<p class="foot-h">Services</p>\s*<ul>\n).*?(\n\s*</ul>)', lambda m: m.group(1) + foot_services + m.group(2), h, count=1, flags=re.S)
assert n_ == 1, 'footer services list not found'

# areas: scrolling strip (JS) + plain crawlable list under the postcode checker
marquee = sorted(AREAS.items(), key=lambda kv: hashlib.sha1(kv[0].encode()).hexdigest())
h, n_ = re.subn(r'  const AREAS = \[.*?\];', lambda m: '  const AREAS = ' + json.dumps([[a['short'], s] for s, a in marquee], ensure_ascii=False, separators=(',', ':')) + ';', h, count=1)
assert n_ == 1, 'const AREAS not found'
area_links = ''.join(f'<li><a href="/areas/{slug}/">{esc(a["name"])}</a></li>' for slug, a in AREAS.items())
area_block = ('\n    <nav class="area-links" aria-label="Areas we cover"><strong>Local cleaners in:</strong> <ul>' + area_links +
              '</ul> — <a href="/areas/">all areas</a></nav>\n    ')
if '<!-- area-links:start -->' not in h:
    h = h.replace('<p id="postcode-result"></p>', '<p id="postcode-result"></p>\n    <!-- area-links:start --><!-- area-links:end -->', 1)
h = replace_block(h, 'area-links', area_block)

write('index.html', h)
print(f'index.html: {len(h.encode()) // 1024} KB, {len(GALLERY)} gallery photos, {len(AREAS)} areas')

# ====================================================================== 4. shared CSS
css = re.search(r'<style>\n(.*?)</style>', h, flags=re.S).group(1)
css += '''
/* ================= generated pages (services, areas, policies) ================= */
.sp-hero { padding: 140px 0 40px; }
.crumbs { font-size: 12.5px; color: var(--ink-soft); margin-bottom: 18px; letter-spacing: .02em; }
.crumbs a { color: var(--pine-deep); text-decoration: underline; text-underline-offset: 3px; }
.sp-lede { font-family: var(--font-display); font-weight: 800; font-size: clamp(1.2rem, 2.6vw, 1.5rem); color: var(--ink); line-height: 1.2; margin-bottom: 14px; max-width: 640px; }
.sp-hero .sp-tag a, .sp-body p a { color: var(--pine-deep); text-decoration: underline; text-underline-offset: 3px; }
.sp-body h2 { font-family: var(--font-body); font-weight: 700; font-size: 1.25rem; margin: 40px 0 18px; }
.sp-body h3 { font-size: 1.04rem; }
.sp-body ul.plain { margin: 0 0 18px 20px; color: var(--ink-soft); }
.sp-body ul.plain li { margin-bottom: 6px; }
.svc-list { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.svc-list a { display: flex; justify-content: space-between; gap: 10px; background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 12px 16px; font-size: 14px; transition: .3s var(--ease); }
.svc-list a:hover { border-color: var(--pine); transform: translateY(-2px); }
.svc-list a span { color: var(--pine-deep); font-weight: 600; white-space: nowrap; }
.near-links a { display: inline-block; background: var(--mint); color: var(--moss); border-radius: 999px; padding: 8px 16px; font-size: 13px; font-weight: 500; margin: 0 8px 8px 0; transition: .25s; }
.near-links a:hover { background: var(--pine); color: #fff; }
.review-strip { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 18px; background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 16px 20px; margin: 0 0 26px; font-size: 14px; }
.review-strip .stars, .quote-card .stars { color: var(--gold); letter-spacing: 2px; font-size: 16px; }
.review-strip a { color: var(--pine-deep); font-weight: 600; text-decoration: underline; }
/* photos */
.sp-figs { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 30px 0 8px; }
.sp-figs figure { margin: 0; background: var(--card); border: 1px solid var(--line); border-radius: 16px; overflow: hidden; }
.sp-figs figure.wide { grid-column: 1 / -1; }
.sp-figs img { display: block; width: 100%; height: auto; aspect-ratio: 3 / 2; object-fit: cover; background: #E8EFEA; }
.sp-figs figure.natural { max-width: 680px; }
.sp-figs figure.natural img { aspect-ratio: auto; }
.sp-figs figcaption { font-size: 12.5px; color: var(--ink-soft); padding: 10px 14px 12px; line-height: 1.5; }
/* tables */
.table-wrap { overflow-x: auto; }
.sp-body .eot-table td, .sp-body .eot-table th { padding: 14px 18px; }
.eot-table td a { text-decoration: underline; text-underline-offset: 3px; }
.eot-table td a:hover { color: var(--pine-deep); }
.sp-body .small-note { max-width: 680px; }
/* customer quote */
.quote-card { margin: 30px 0 0; background: var(--mint); border-radius: 16px; padding: 22px 24px; }
.quote-card blockquote { font-size: 1.02rem; line-height: 1.6; color: var(--moss); margin: 8px 0 10px; }
.quote-card figcaption { font-size: 12.5px; color: var(--ink-soft); }
.quote-card figcaption strong { color: var(--pine-deep); }
/* area pages */
.facts { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 4px 20px; }
.facts > div { display: grid; grid-template-columns: 150px 1fr; gap: 14px; padding: 13px 0; border-bottom: 1px solid var(--line); font-size: 14px; }
.facts > div:last-child { border-bottom: none; }
.facts dt { color: var(--ink-soft); font-size: 11.5px; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; padding-top: 3px; }
.facts dd { color: var(--ink); }
.facts dd a { color: var(--pine-deep); text-decoration: underline; text-underline-offset: 3px; }
.svc-feat { display: grid; gap: 12px; margin-bottom: 14px; }
.svc-feat-item { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 18px 20px; transition: border-color .3s, transform .35s var(--ease); }
.svc-feat-item:hover { border-color: rgba(20,122,75,.4); transform: translateX(4px); }
.svc-feat-item h3 { margin-bottom: 6px; }
.svc-feat-item h3 a:hover { color: var(--pine-deep); }
.sp-body .svc-feat-item p { font-size: 14px; margin-bottom: 8px; }
.svc-feat-item .pr { font-size: 13px; font-weight: 600; color: var(--pine-deep); }
.sp-body .also { font-size: 13.5px; margin: 18px 0 10px; }
.know { list-style: none; display: grid; gap: 12px; max-width: 680px; }
.know li { position: relative; padding-left: 24px; color: var(--ink-soft); font-size: 15px; }
.know li::before { content: ''; position: absolute; left: 3px; top: .62em; width: 8px; height: 8px; border-radius: 50%; background: var(--pine); }
.know li strong { color: var(--ink); }
/* areas index */
.area-group { padding-bottom: 46px; }
.area-group h2 { font-family: var(--font-body); font-weight: 700; font-size: 1.25rem; margin-bottom: 6px; }
.area-group > p { color: var(--ink-soft); font-size: 14.5px; margin-bottom: 18px; }
.area-index { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; }
.area-index a { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; transition: .3s var(--ease); }
.area-index a:hover { border-color: var(--pine); transform: translateY(-2px); }
.area-index a small { display: block; color: var(--ink-soft); font-size: 12px; margin-top: 2px; }
/* services hub */
.hub-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.hub-card { background: var(--card); border: 1px solid var(--line); border-radius: var(--r); padding: 24px 24px 20px; display: flex; flex-direction: column; gap: 8px; transition: transform .45s var(--ease), border-color .3s, box-shadow .45s var(--ease); }
.hub-card:hover { transform: translateY(-4px); border-color: rgba(20,122,75,.4); box-shadow: 0 14px 34px rgba(18,36,27,.07); }
.hub-card h2 { font-family: var(--font-body); font-weight: 700; font-size: 1.14rem; letter-spacing: -0.01em; }
.hub-card h2 a:hover { color: var(--pine-deep); }
.hub-card p { font-size: 14px; color: var(--ink-soft); flex: 1; }
.hub-card .pr { font-weight: 700; font-size: 1.1rem; color: var(--pine-deep); }
.hub-card .pr small { font-weight: 400; font-size: 12.5px; color: var(--ink-soft); }
.hub-card .links { display: flex; gap: 18px; font-size: 12px; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; margin-top: 6px; }
.hub-card .links a { color: var(--pine-deep); }
.hub-card .links a:hover { text-decoration: underline; text-underline-offset: 4px; }
.hub-section { padding: 30px 0 0; }
.hub-section h2 { font-family: var(--font-body); font-weight: 700; font-size: 1.35rem; margin-bottom: 16px; }
.which { list-style: none; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.which li { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px 18px; font-size: 14px; color: var(--ink-soft); }
.which li a { display: block; color: var(--pine-deep); font-weight: 600; margin-top: 2px; }
.which li a:hover { text-decoration: underline; text-underline-offset: 3px; }
.steps { list-style: none; counter-reset: step; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.steps li { counter-increment: step; background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px 18px; font-size: 14px; color: var(--ink-soft); }
.steps li::before { content: counter(step); display: grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; background: var(--mint); color: var(--pine-deep); font-weight: 700; font-size: 13px; margin-bottom: 10px; }
.steps li strong { display: block; color: var(--ink); margin-bottom: 2px; }
/* policies + 404 */
.policy { padding-bottom: 90px; max-width: 760px; }
.policy p { color: var(--ink-soft); margin-bottom: 18px; }
.policy p strong { color: var(--ink); }
.nf-links { display: flex; gap: 12px; flex-wrap: wrap; margin: 28px 0 18px; }
@media (max-width: 960px) { .steps { grid-template-columns: 1fr 1fr; } }
@media (max-width: 760px) { .svc-list, .hub-grid, .which { grid-template-columns: 1fr; } .sp-hero { padding-top: 110px; } }
@media (max-width: 520px) { .steps { grid-template-columns: 1fr; } }
@media (max-width: 620px) { .facts > div { grid-template-columns: 1fr; gap: 2px; } .sp-figs { grid-template-columns: 1fr; } }
'''
write('assets/site.css', css)

# ====================================================================== 5. page shell
header_html = re.search(r'(<div class="scroll-progress".*?</div>\n\n)<main', h, flags=re.S).group(1)
footer_html = re.search(r'(<!-- ============ FOOTER ============ -->.*?</a>\n)<script>', h, flags=re.S).group(1)
NAV_TARGET = {'': '/', 'top': '/', 'services': '/services/', 'areas': '/areas/', 'prices': '/services/#prices'}
def absolutise(frag):
    """Homepage section links (#services ...) become real addresses on the generated pages."""
    frag = re.sub(r'href="#(?!/)([a-z]*)"', lambda m: f'href="{NAV_TARGET.get(m.group(1), "/#" + m.group(1))}"', frag)
    return frag.replace('href="#/privacy"', 'href="/privacy/"').replace('href="#/legal"', 'href="/legal/"')
header_html, footer_html = absolutise(header_html), absolutise(footer_html)

def header_for(section):
    if not section: return header_html
    target = {'services': '/services/', 'areas': '/areas/'}[section]
    return header_html.replace(f'<li><a href="{target}">', f'<li><a class="active" aria-current="page" href="{target}">', 1)

page_js = '''<script>
(function(){
  var header=document.querySelector('.site-header'),bar=document.querySelector('.scroll-progress');
  function onScroll(){header.classList.toggle('scrolled',window.scrollY>20);var h=document.documentElement.scrollHeight-window.innerHeight;bar.style.width=(h>0?(window.scrollY/h)*100:0)+'%';}
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();
  var burger=document.querySelector('.burger'),nav=document.querySelector('.mobile-nav');
  burger.addEventListener('click',function(){burger.classList.toggle('open');nav.classList.toggle('open');document.body.style.overflow=nav.classList.contains('open')?'hidden':'';});
  document.querySelectorAll('.faq-q').forEach(function(btn){btn.addEventListener('click',function(){var item=btn.closest('.faq-item'),a=item.querySelector('.faq-a'),open=item.classList.contains('open');item.parentElement.querySelectorAll('.faq-item.open').forEach(function(o){o.classList.remove('open');o.querySelector('.faq-a').style.maxHeight=null;o.querySelector('.faq-q').setAttribute('aria-expanded','false');});if(!open){item.classList.add('open');a.style.maxHeight=a.scrollHeight+'px';btn.setAttribute('aria-expanded','true');}});});
})();
</script>'''

def shell(url, title, desc, body, ld=(), section=None, image=None, image_alt=None, robots='index, follow, max-image-preview:large', head_extra=''):
    return f'''<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{head_extra}<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-192.png" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#147A4B">
{seo_head(url, title, desc, ld, image, image_alt, robots)}
</head>
<body>
{header_for(section)}<main id="top">
{body}
</main>
{footer_html}{page_js}
</body>
</html>
'''

def crumbs(items):
    """items: [(name, path)] — visible trail + BreadcrumbList structured data."""
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + p} for i, (n, p) in enumerate(items)]}
    trail = ' › '.join(f'<a href="{p}">{esc(n)}</a>' if i < len(items) - 1 else f'<span aria-current="page">{esc(n)}</span>'
                       for i, (n, p) in enumerate(items))
    return f'<nav class="crumbs" aria-label="Breadcrumb">{trail}</nav>', ld

tick = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>'
review_strip = ('<div class="review-strip"><span class="stars" aria-hidden="true">★★★★★</span><span><strong>5-star rated on Google</strong> by our customers</span>'
                f'<a href="{BIZ["gbp"]}" target="_blank" rel="noopener">Read our Google reviews</a></div>')
def wa_link(text): return f'https://wa.me/{BIZ["whatsapp"]}?text={quote(text, safe="")}'
def faq_html(items):
    return '<div class="sp-faq">' + ''.join(
        f'<div class="faq-item"><button class="faq-q" aria-expanded="false">{amp(q)}<span class="faq-icon" aria-hidden="true">+</span></button>'
        f'<div class="faq-a"><p>{amp(a)}</p></div></div>' for q, a in items) + '</div>'
def service_links(exclude=()):
    return '<div class="svc-list">' + ''.join(
        f'<a href="/services/{slug}/">{SHORT_NAME[sid]}<span>{price_line(sid)}</span></a>'
        for slug, sid, _, _ in SERVICE_META if sid not in exclude) + '</div>'
def area_pills(slugs):
    return '<div class="near-links">' + ''.join(f'<a href="/areas/{s}/">{esc(AREAS[s]["name"])}</a>' for s in slugs) + '</div>'
def fixed_table():
    rows = ''.join(
        f'<tr><td>{EOT_LABELS[k]}</td>' + (f'<td class="p">From {money(v[0])}</td><td class="p">From {money(v[1])}</td>' if v else
                                           '<td class="p">Individual quote</td><td class="p">Individual quote</td>') + '</tr>'
        for k, v in EOT_PRICES.items())
    return ('<div class="table-wrap"><table class="eot-table"><thead><tr><th>Property size</th><th>Without carpet cleaning</th>'
            f'<th>With carpet cleaning</th></tr></thead><tbody>{rows}</tbody></table></div>')
def hourly_table(sid):
    s = SERVICES[sid]
    rows = ''.join(f'<tr><td>{hrs} hours</td><td class="p">{money(max(s["rate"] * hrs, s["min"]))}</td></tr>'
                   for hrs in range(s['minH'], s['minH'] + 4))
    return ('<div class="table-wrap"><table class="eot-table"><thead><tr><th>Length of visit</th><th>Price for one cleaner</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')
def fixed_price_sentence():
    with_c = [f'{EOT_LABELS[k].lower()} {money(v[0])}' for k, v in EOT_PRICES.items() if v]
    return join_and(with_c)

urls = []            # (url, file, [image urls])
def emit(path, url, htmltext, images=()):
    write(path, htmltext)
    urls.append((url, path, list(images)))

# ====================================================================== 6. service pages
SERVICE_PHOTOS = {k: v for k, v in PHOTOS.get('service_photos', {}).items() if not k.startswith('_')}
top_areas = ['sunbury-on-thames', 'shepperton', 'staines', 'walton-on-thames', 'hampton', 'feltham', 'kingston', 'twickenham', 'richmond', 'wimbledon', 'putney', 'ealing']

def service_price_block(sid, name):
    s = SERVICES[sid]
    if is_fixed(sid):
        return (f'<h2 id="prices">{name} prices</h2>\n'
                f'<p>{name} is a fixed price based on the size of the property, not an hourly rate — so you know the cost before we start, however long the job takes.</p>\n'
                f'{fixed_table()}\n'
                '<p class="small-note"><strong>Prices are for one professional cleaner</strong> and include eco-friendly products and equipment. '
                'Homes with four or more bedrooms are quoted individually. No deposit — you pay after the clean.</p>')
    return (f'<h2 id="prices">{name} prices</h2>\n'
            f'<p>{name} costs <strong>{money(s["rate"])} per hour</strong> for one professional cleaner, with a minimum of {s["minH"]} hours ({money(s["min"])}). '
            'Eco-friendly products and equipment are included, there is no deposit, and you pay after the clean.</p>\n'
            f'{hourly_table(sid)}\n'
            '<p class="small-note">Not sure how long you need? Tell us the number of bedrooms and bathrooms when you book and we’ll recommend the hours.</p>')

def service_price_faq(sid, name):
    s = SERVICES[sid]
    if is_fixed(sid):
        return (f'How much does {name.lower()} cost?',
                f'It is a fixed price by property size: {fixed_price_sentence()}, with professional carpet cleaning available for a fixed supplement. '
                'Homes with four or more bedrooms are quoted individually. Prices are for one professional cleaner and include products and equipment.')
    return (f'How much does {name.lower()} cost?',
            f'{money(s["rate"])} per hour for one professional cleaner, with a minimum of {s["minH"]} hours ({money(s["min"])}). '
            'Eco-friendly products and equipment are included, and you pay after the clean.')

def service_figs(sid):
    files = SERVICE_PHOTOS.get(sid, [])
    if not files: return '', []
    ps = [PHOTO_BY_FILE[f] for f in files]
    out = []
    for i, p in enumerate(ps):
        wide = (i == 0 and len(ps) != 2)
        cls = 'wide' + (' natural' if len(ps) == 1 else '') if wide else ''
        sizes = '(max-width: 760px) 92vw, 680px' if wide else '(max-width: 620px) 92vw, 340px'
        out.append(f'<figure{" class=" + chr(34) + cls + chr(34) if cls else ""}>{picture(p, sizes)}<figcaption>{esc(p["caption"])}</figcaption></figure>')
    return '<div class="sp-figs">' + ''.join(out) + '</div>', [f'{SITE}/img/{p["file"]}' for p in ps]

def price_card(sid, sp):
    head = (f'<div class="from">Fixed prices</div><div class="amt">{money(FIXED_FROM)} <small>from</small></div>' if is_fixed(sid) else
            f'<div class="from">From</div><div class="amt">{money(SERVICES[sid]["rate"])} <small>/hour</small></div>')
    head += '<div class="from" style="margin-top:6px;text-transform:none;letter-spacing:0">Price for one professional cleaner</div>'
    rows = ''.join(f'<div class="sp-price-row"><span>{amp(r[0])}</span><strong>{amp(r[1])}</strong></div>' for r in sp['rows'])
    return (f'<aside class="sp-price-card" aria-label="Prices and booking"><div class="sp-price-head">{head}</div><div class="sp-price-body">{rows}'
            f'<a class="btn btn-solid" href="/#book-{sid}">Book this clean <span class="arr">→</span></a>'
            f'<div class="sp-wa-line">or <a href="{esc(wa_link("Hi Urban Gleam, I’d like a quote for " + SHORT_NAME[sid].lower()))}" target="_blank" rel="noopener">ask us on WhatsApp</a>'
            f' · <a href="tel:{BIZ["phone_e164"]}">{BIZ["phone_display"]}</a></div></div></aside>')

for slug, sid, title, desc in SERVICE_META:
    sp = SP[sid]
    url = f'{SITE}/services/{slug}/'
    name = SHORT_NAME[sid]
    c_html, c_ld = crumbs([('Home', '/'), ('Services', '/services/'), (name, f'/services/{slug}/')])
    faqs = [tuple(f) for f in sp['faqs']] + [service_price_faq(sid, name)]
    figs, imgs = service_figs(sid)
    revs = reviews_for_service(sid)[:1]
    svc_ld = {"@context": "https://schema.org", "@type": "Service", "@id": url + '#service', "name": name, "serviceType": name,
              "url": url, "description": desc, "provider": biz_ref(),
              "areaServed": [{"@type": "AdministrativeArea", "name": "Greater London"}, {"@type": "AdministrativeArea", "name": "Surrey"}],
              "offers": ld_offer(sid)}
    if imgs: svc_ld["image"] = imgs
    body = f'''<section class="sp-hero"><div class="container">
{c_html}
<span class="eyebrow" style="display:flex">{amp(sp['cat'])}</span>
<h1>{name} in London, Surrey &amp; the M25</h1>
<p class="sp-lede">{amp(sp['h'])}</p>
<p class="sp-tag">{amp(sp['tag'])}</p>
</div></section>
<div class="container sp-grid">
<div class="sp-body">
{review_strip}
{''.join('<p>' + amp(p) + '</p>' for p in sp['intro'])}
<p>{ALSO_KNOWN_AS[sid]}</p>
{figs}
<h2>What’s included</h2>
<div class="sp-includes">{''.join(f'<div class="sp-inc">{tick}<span>{amp(i)}</span></div>' for i in sp['includes'])}</div>
{service_price_block(sid, name)}
<h2>Perfect for</h2>
<div class="sp-perfect">{''.join(f'<span>{amp(p)}</span>' for p in sp['perfect'])}</div>
{''.join(quote_card(r) for r in revs)}
<h2>Where we offer {name.lower()}</h2>
<p>Our team is based in Sunbury-on-Thames and works across South West London, Surrey and everywhere inside the M25 — including:</p>
{area_pills(top_areas)}
<p><a href="/areas/">See all the areas we cover →</a></p>
<h2>Common questions</h2>
{faq_html(faqs)}
<div class="sp-note">{amp(sp['note'])}</div>
<h2>Other cleaning services</h2>
{service_links((sid,))}
<p><a href="/services/">Compare all services and prices →</a></p>
</div>
{price_card(sid, sp)}
</div>'''
    og = (imgs[0], PHOTO_BY_FILE[SERVICE_PHOTOS[sid][0]]['w'], PHOTO_BY_FILE[SERVICE_PHOTOS[sid][0]]['h']) if imgs else None
    og_alt = PHOTO_BY_FILE[SERVICE_PHOTOS[sid][0]]['alt'] if imgs else None
    emit(f'services/{slug}/index.html', url,
         shell(url, title + ' | Urban Gleam', desc, body, [svc_ld, c_ld, ld_faq(faqs)], 'services', og, og_alt), imgs)

# ---------------------------------------------------------------------- services hub
url = SITE + '/services/'
c_html, c_ld = crumbs([('Home', '/'), ('Services', '/services/')])
hub_cards = ''.join(
    f'<article class="hub-card"><h2><a href="/services/{slug}/">{SHORT_NAME[sid]}</a></h2><p>{HUB_LINE[sid]}</p>'
    f'<div class="pr">{price_line(sid).capitalize()} <small>· {min_line(sid).lower()}</small></div>'
    f'<div class="links"><a href="/services/{slug}/" aria-label="{SHORT_NAME[sid]}: what’s included">What’s included</a>'
    f'<a href="/#book-{sid}" aria-label="Book {SHORT_NAME[sid].lower()}">Book →</a></div></article>'
    for slug, sid, _, _ in SERVICE_META)
hourly_rows = ''.join(
    f'<tr><td><a href="/services/{slug}/">{SHORT_NAME[sid]}</a></td><td class="p">{money(SERVICES[sid]["rate"])} per hour</td>'
    f'<td>{SERVICES[sid]["minH"]} hours · {money(SERVICES[sid]["min"])}</td></tr>'
    for slug, sid, _, _ in SERVICE_META if not is_fixed(sid))
which = ''.join(f'<li>{q}<a href="/services/{SLUG_BY_ID[sid]}/">{SHORT_NAME[sid]} →</a></li>' for q, sid in WHICH_CLEAN)
hourly_from = min(SERVICES[sid]['rate'] for _, sid, _, _ in SERVICE_META if not is_fixed(sid))
hub_desc = (f'All eight Urban Gleam cleaning services and their prices: domestic cleaning from {money(hourly_from)}/hr, office from '
            f'{money(SERVICES["office"]["rate"])}/hr, end of tenancy and after builders fixed from {money(FIXED_FROM)}.')
body = f'''<section class="sp-hero"><div class="container">
{c_html}
<span class="eyebrow" style="display:flex">Services &amp; prices</span>
<h1>Cleaning services and <span class="accent-g">prices.</span></h1>
<p class="sp-tag">Eight services, one clear price list. Every price is for one professional cleaner and includes eco-friendly products and equipment. There are no deposits, and you pay after your clean.</p>
</div></section>
<div class="container" style="padding-bottom:90px">
<div class="hub-grid">{hub_cards}</div>
<section class="hub-section" id="prices">
<h2>Hourly rates</h2>
<div class="table-wrap"><table class="eot-table"><thead><tr><th>Service</th><th>Rate for one cleaner</th><th>Minimum visit</th></tr></thead><tbody>{hourly_rows}</tbody></table></div>
</section>
<section class="hub-section">
<h2>Fixed prices: end of tenancy and after builders cleaning</h2>
{fixed_table()}
<p class="small-note">The same fixed prices apply to <a href="/services/end-of-tenancy-cleaning/">end of tenancy cleaning</a> and <a href="/services/after-builders-cleaning/">after builders cleaning</a>. Hourly services exclude professional window, carpet and upholstery cleaning — ask us for a quote.</p>
</section>
<section class="hub-section">
<h2>Which clean do I need?</h2>
<ul class="which">{which}</ul>
</section>
<section class="hub-section">
<h2>How booking works</h2>
<ol class="steps">{''.join(f'<li><strong>{t}.</strong> {d}</li>' for t, d in HOW_BOOKING_WORKS)}</ol>
<p style="margin-top:18px"><a class="btn btn-solid" href="/#book">Book a clean <span class="arr">→</span></a></p>
</section>
<section class="hub-section">
<h2>Where we work</h2>
<p style="color:var(--ink-soft);max-width:680px;margin-bottom:16px">We’re based in Sunbury-on-Thames and clean homes and offices across South West London, Surrey and everywhere inside the M25.</p>
{area_pills(top_areas)}
<p style="margin-top:8px"><a href="/areas/" style="color:var(--pine-deep);text-decoration:underline;text-underline-offset:3px">See all the areas we cover →</a></p>
</section>
</div>'''
emit('services/index.html', url, shell(url, 'Cleaning Services & Prices in London & Surrey | Urban Gleam', hub_desc, body, [c_ld], 'services'))

# ====================================================================== 7. area pages
def area_title(a): return f'Cleaners in {a["name"]} ({a["pc"]})'
def area_desc(a):
    for n in (3, 2):
        d = (f'Local cleaners in {a["name"]} ({a["pc"]}), covering {join_and(a["hoods"][:n])}. Domestic cleaning from '
             f'{money(SERVICES["domestic"]["rate"])}/hr, end of tenancy from {money(FIXED_FROM)}. Book online.')
        if len(d) <= 160: return d
    return d.replace(' Book online.', '')

groups_html = ''
for g in GROUPS:
    members = [(s, a) for s, a in AREAS.items() if a['group'] == g['name']]
    cards = ''.join(
        f'<a href="/areas/{s}/"><strong>Cleaners in {esc(a["name"])}</strong><small>{esc(a["pc"])} · '
        + ('where we’re based' if s == HOME_AREA else f'{distance_phrase(a)} from our base' if near_base(a) else esc(', '.join(a['hoods'][:2]))) + '</small></a>'
        for s, a in members)
    groups_html += f'<section class="area-group"><h2>{esc(g["name"])}</h2><p>{esc(g["intro"])}</p><div class="area-index">{cards}</div></section>\n'
url = SITE + '/areas/'
c_html, c_ld = crumbs([('Home', '/'), ('Areas', '/areas/')])
body = f'''<section class="sp-hero"><div class="container">
{c_html}
<span class="eyebrow" style="display:flex">Coverage</span>
<h1>Areas we cover in London &amp; <span class="accent-g">Surrey.</span></h1>
<p class="sp-tag">Urban Gleam is based in Sunbury-on-Thames and cleans homes and offices across South West London, Surrey and everywhere inside the M25. Pick your area for local details and prices, or <a href="/#areas">check your postcode</a> on the homepage.</p>
</div></section>
<div class="container" style="padding-bottom:50px">
{groups_html}<p class="small-note" style="margin-top:0">Don’t see your town? We cover most postcodes inside the M25 — call <a href="tel:{BIZ['phone_e164']}">{BIZ['phone_display']}</a> or <a href="/#book">book online</a> with your postcode.</p>
</div>'''
emit('areas/index.html', url, shell(url, 'Areas We Cover: Cleaners in London & Surrey | Urban Gleam',
     'Find your local Urban Gleam cleaners across South West London and Surrey — from our base in Sunbury-on-Thames to Chelsea, Croydon and Epsom.',
     body, [c_ld], 'areas'))

for slug, a in AREAS.items():
    url = f'{SITE}/areas/{slug}/'
    name, short = a['name'], a['short']
    dist = distance_phrase(a)
    c_html, c_ld = crumbs([('Home', '/'), ('Areas', '/areas/'), (name, f'/areas/{slug}/')])
    feat = ''.join(
        f'<div class="svc-feat-item"><h3><a href="/services/{SLUG_BY_ID[sid]}/">{SHORT_NAME[sid]} in {esc(short)}</a></h3>'
        f'<p>{amp(fill(line))}</p><span class="pr">{price_line(sid).capitalize()} · {min_line(sid).lower()}</span></div>'
        for sid, line in a['focus'].items())
    know = ''.join(f'<li>{amp(fill(k))}</li>' for k in [f'<strong>Parking and access.</strong> {a["parking"]}'] + a['know'])
    rev = review_for_area(a)
    faqs = [
        (f'Which parts of {name} do you cover?',
         f'All of {a["pc"]}, including {join_and(a["hoods"])}. If you’re not sure, <a href="/#areas">check your postcode</a> or call {BIZ["phone_display"]}.'),
        (f'How much does a cleaner cost in {name}?',
         f'Regular domestic cleaning is {money(SERVICES["domestic"]["rate"])} per hour (minimum {money(SERVICES["domestic"]["min"])}), one-off and spring cleans are '
         f'{money(SERVICES["oneoff"]["rate"])} per hour, and end of tenancy and after-builders cleans are a fixed price from {money(FIXED_FROM)}. '
         f'Prices are for one professional cleaner and are the same in every area we cover — see <a href="/services/#prices">all prices</a>.'),
        (f'How soon can you start in {name}?',
         (f'Our office is in {short} itself, so this is where we can be quickest. ' if slug == HOME_AREA else
          f'{name} is {dist} from our base in Sunbury-on-Thames. ' if near_base(a) else '') +
         'Regular cleans usually start within a few days, and one-off, end of tenancy and emergency cleans can often be arranged within 24–48 hours.'),
    ]
    local_ld = {"@context": "https://schema.org", "@type": "Service", "@id": url + '#service', "name": f"Cleaning services in {name}", "serviceType": "Cleaning service",
                "url": url, "description": area_desc(a), "provider": biz_ref(),
                "areaServed": {"@type": "Place", "name": name, "geo": {"@type": "GeoCoordinates", "latitude": a['lat'], "longitude": a['lng']},
                               "containedInPlace": {"@type": "Country", "name": "United Kingdom"}}}
    base_line = ('Our office is here, on Kings Avenue (TW16 7QE)' if slug == HOME_AREA
                 else f'{dist.capitalize()} from our office in <a href="/areas/{HOME_AREA}/">Sunbury-on-Thames</a>')
    team = PHOTO_BY_FILE[PHOTOS['team_photo']]
    body = f'''<section class="sp-hero"><div class="container">
{c_html}
<span class="eyebrow" style="display:flex">Local cleaners · {esc(a['pc'])}</span>
<h1>Cleaners in {esc(name)}</h1>
<p class="sp-lede">Eco-friendly home, office &amp; end of tenancy <span class="accent">cleaning.</span></p>
<p class="sp-tag">Vetted, insured local cleaners covering {esc(', '.join(a['hoods'][:3]))} and the rest of {esc(a['pc'])}. Transparent prices from {money(SERVICES['domestic']['rate'])}/hr, the same trusted cleaner every visit, and online booking in two minutes.</p>
</div></section>
<div class="container sp-grid">
<div class="sp-body">
{review_strip}
<p>{amp(fill(a['blurb']))}</p>
<p>We clean {amp(a['homes'])} — from a two-hour weekly tidy to a full agency-standard end of tenancy clean. <strong>Every visit uses non-toxic, biodegradable products</strong> and HEPA-filter vacuums.</p>
<h2>Where we clean in {esc(short)}</h2>
<dl class="facts">
<div><dt>Postcodes</dt><dd>{esc(a['pc'])}</dd></div>
<div><dt>Neighbourhoods</dt><dd>{esc(', '.join(a['hoods']))}</dd></div>
<div><dt>Local council</dt><dd>{esc(a['council'])}</dd></div>
{f'<div><dt>From our base</dt><dd>{base_line}</dd></div>' if near_base(a) else ''}
</dl>
<h2>Cleaning services in {esc(name)}</h2>
<div class="svc-feat">{feat}</div>
<p class="also">Also available in {esc(short)}:</p>
{service_links(tuple(a['focus']))}
<h2>Good to know before you book in {esc(short)}</h2>
<ul class="know">{know}</ul>
{quote_card(rev) if rev else ''}
<div class="sp-figs"><figure class="wide natural">{picture(team, '(max-width: 760px) 92vw, 680px')}<figcaption>{esc(team['caption'])}</figcaption></figure></div>
<h2>Why choose Urban Gleam</h2>
<div class="sp-includes">
<div class="sp-inc">{tick}<span>Same trusted cleaner for regular weekly or fortnightly visits</span></div>
<div class="sp-inc">{tick}<span>Vetted, background-checked and fully insured cleaners</span></div>
<div class="sp-inc">{tick}<span>No deposits — you pay after your clean</span></div>
<div class="sp-inc">{tick}<span>Open {BIZ['hours_text']}, 7 days a week</span></div>
</div>
<h2>Common questions</h2>
{faq_html(faqs)}
<h2>Nearby areas we also cover</h2>
{area_pills(a['near'])}
<p><a href="/areas/">All the areas we cover →</a></p>
</div>
<aside class="sp-price-card" aria-label="Prices and booking"><div class="sp-price-head"><div class="from">Cleaners in {esc(short)}</div><div class="amt">{money(SERVICES['domestic']['rate'])} <small>/hour</small></div><div class="from" style="margin-top:6px;text-transform:none;letter-spacing:0">Domestic cleaning · one professional cleaner</div></div>
<div class="sp-price-body">
<div class="sp-price-row"><span>Domestic cleaning</span><strong>{money(SERVICES['domestic']['rate'])}/hr · min {money(SERVICES['domestic']['min'])}</strong></div>
<div class="sp-price-row"><span>Office cleaning</span><strong>{money(SERVICES['office']['rate'])}/hr · min {money(SERVICES['office']['min'])}</strong></div>
<div class="sp-price-row"><span>Spring / one-off deep clean</span><strong>{money(SERVICES['oneoff']['rate'])}/hr · min {SERVICES['oneoff']['minH']} hrs</strong></div>
<div class="sp-price-row"><span>End of tenancy</span><strong>Fixed from {money(FIXED_FROM)}</strong></div>
<div class="sp-price-row"><span>After builders</span><strong>Fixed from {money(FIXED_FROM)}</strong></div>
<div class="sp-price-row"><span>Emergency / same-day</span><strong>{money(SERVICES['emergency']['rate'])}/hr · min {money(SERVICES['emergency']['min'])}</strong></div>
<a class="btn btn-solid" href="/#book">Book a clean in {esc(short)} <span class="arr">→</span></a>
<div class="sp-wa-line">or <a href="{esc(wa_link('Hi Urban Gleam, I’d like a cleaning quote in ' + name))}" target="_blank" rel="noopener">ask us on WhatsApp</a> · <a href="tel:{BIZ['phone_e164']}">{BIZ['phone_display']}</a></div>
</div></aside>
</div>'''
    emit(f'areas/{slug}/index.html', url, shell(url, area_title(a) + ' | Urban Gleam', area_desc(a), body, [local_ld, c_ld], 'areas'))

# ====================================================================== 8. privacy, legal, 404, old addresses
for key, slug, title, desc in (
        ('privacy', 'privacy', 'Privacy Policy | Urban Gleam', 'How Urban Gleam Ltd collects, uses and stores the details you give us when you book or enquire about a clean.'),
        ('legal', 'legal', 'Legal Notice | Urban Gleam', f'Company details and service terms for Urban Gleam Ltd, {BIZ["street"]}, {BIZ["town"]} {BIZ["postcode"]}.')):
    d = STATIC[key]
    url = f'{SITE}/{slug}/'
    c_html, c_ld = crumbs([('Home', '/'), (strip_tags(d['title']).rstrip('.'), f'/{slug}/')])
    body = (f'<section class="sp-hero"><div class="container">\n{c_html}\n<h1>{d["title"]}</h1>\n</div></section>\n'
            '<div class="container policy">\n' + '\n'.join('<p>' + amp(p) + '</p>' for p in d['body']) + '\n</div>')
    emit(f'{slug}/index.html', url, shell(url, title, desc, body, [c_ld]))

body = f'''<section class="sp-hero" style="padding-bottom:110px"><div class="container">
<span class="eyebrow" style="display:flex">Page not found</span>
<h1>We couldn’t find that <span class="accent">page.</span></h1>
<p class="sp-tag">The link may be out of date, or the address may have been mistyped. Try one of these instead:</p>
<div class="nf-links"><a class="btn btn-solid" href="/">Homepage</a><a class="btn btn-line" href="/services/">Services &amp; prices</a><a class="btn btn-line" href="/areas/">Areas we cover</a><a class="btn btn-line" href="/#book">Book a clean</a></div>
<p class="sp-tag">Or call us on <a href="tel:{BIZ['phone_e164']}">{BIZ['phone_display']}</a>.</p>
</div></section>'''
write('404.html', shell(None, 'Page not found | Urban Gleam', 'Sorry — that page doesn’t exist. Find our cleaning services, prices and the areas we cover from the homepage.',
                        body, robots='noindex, follow', head_extra=guard_js(False) + '\n'))

for old, new in MOVED.items():
    canonical = SITE + new.split('#')[0]
    write(f'{old.strip("/")}/index.html', f'''<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>This page has moved | Urban Gleam</title>
<link rel="canonical" href="{canonical}">
<meta http-equiv="refresh" content="0; url={new}">
</head>
<body>
<p>This page has moved. <a href="{new}">Continue to the new page</a>.</p>
</body>
</html>
''')

# remove pages for areas/services that no longer exist
keep = {os.path.dirname(f) for _, f, _ in urls}
for parent in ('areas', 'services'):
    for d in os.listdir(parent):
        p = os.path.join(parent, d)
        if os.path.isdir(p) and p not in keep and os.listdir(p) == ['index.html']:
            shutil.rmtree(p); print('  removed stale page', p)

# ====================================================================== 9. sitemap + robots
LM_FILE = 'tools/lastmod.json'
LM = json.load(open(LM_FILE)) if os.path.exists(LM_FILE) else {}
def lastmod(url, path):
    digest = hashlib.sha1(read(path).encode()).hexdigest()
    if LM.get(url, {}).get('hash') != digest:
        LM[url] = {'hash': digest, 'lastmod': TODAY}
    return LM[url]['lastmod']
home_images = [f'{SITE}/img/{p["file"]}' for p in GALLERY]
entries = [(SITE + '/', 'index.html', home_images)] + urls
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
for u, path, images in entries:
    imgs = ''.join(f'<image:image><image:loc>{i}</image:loc></image:image>' for i in images)
    sm.append(f'  <url><loc>{u}</loc><lastmod>{lastmod(u, path)}</lastmod>{imgs}</url>')
sm.append('</urlset>\n')
write('sitemap.xml', '\n'.join(sm))
LM = {u: LM[u] for u, _, _ in entries}
json.dump(LM, open(LM_FILE, 'w'), indent=1, sort_keys=True)
write('robots.txt', f'User-agent: *\nAllow: /\nDisallow: /tools/\n\nSitemap: {SITE}/sitemap.xml\n')

# ====================================================================== 10. self-check
problems = []
seen_t, seen_d = {}, {}
for u, path, _ in entries:
    t = re.search(r'<title>(.*?)</title>', read(path)).group(1)
    d = re.search(r'<meta name="description" content="([^"]*)">', read(path)).group(1)
    t, d = html.unescape(t), html.unescape(d)
    if t in seen_t: problems.append(f'same title on {u} and {seen_t[t]}')
    if d in seen_d: problems.append(f'same description on {u} and {seen_d[d]}')
    seen_t[t], seen_d[d] = u, u
    if len(t) > 68: problems.append(f'title is {len(t)} characters (aim for under 65): {u}')
    if len(d) > 165: problems.append(f'description is {len(d)} characters (aim for under 160): {u}')
for s, a in AREAS.items():
    for n in a['near']:
        if n not in AREAS: problems.append(f'areas.json: {s} lists unknown nearby area "{n}"')
    for sid in a['focus']:
        if sid not in SERVICES: problems.append(f'areas.json: {s} features unknown service "{sid}"')
print(f'pages: {len(entries)} in sitemap.xml (+ 404.html and {len(MOVED)} old-address redirects)')
if problems:
    print('\nCHECK THESE:'); [print('  -', p) for p in problems]
