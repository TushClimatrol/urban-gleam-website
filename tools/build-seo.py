#!/usr/bin/env python3
"""Urban Gleam SEO build.

Run from the repo root:  python3 tools/build-seo.py

What it does
  1. Moves the base64 gallery photos in index.html out to /img/*.jpg (page drops from ~2.7 MB to ~150 KB).
  2. Injects SEO head tags + JSON-LD (LocalBusiness, WebSite, FAQPage) into index.html.
  3. Repoints service / area links in index.html at the crawlable static pages.
  4. Writes /assets/site.css (same CSS as index.html) for the static pages.
  5. Generates /services/<slug>/index.html  (8 pages) and /areas/<slug>/index.html (26 pages).
  6. Writes sitemap.xml and robots.txt.

Idempotent: safe to run again after editing index.html, areas.json or the SERVICE_META below.
"""
import base64, html, json, os, re, subprocess, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = 'https://urbangleamcleaning.com'
BIZ = {
    'name': 'Urban Gleam Ltd',
    'short': 'Urban Gleam',
    'phone_display': '07942 369735',
    'phone_e164': '+447942369735',
    'email': 'contact@urbangleamcleaning.com',
    'street': 'Braemar House, Kings Avenue',
    'town': 'Sunbury-on-Thames',
    'county': 'Surrey',
    'postcode': 'TW16 7QE',
    'lat': 51.4268394, 'lng': -0.4221821,
    'gbp': 'https://maps.google.com/?cid=10111168519048199372',
}
TODAY = date.today().isoformat()

# slug, SPA id, page title, meta description, H1 keyword line
SERVICE_META = [
    ('domestic-cleaning',        'domestic',  'Domestic Cleaning London & Surrey from £22.50/hr',
     'Regular weekly or fortnightly home cleaning by the same vetted, insured local cleaner. Eco-friendly products, from £22.50/hr. Book online in 2 minutes — London, Surrey & the M25.'),
    ('office-cleaning',          'office',    'Office Cleaning London & Surrey from £25/hr',
     'Commercial office cleaning — daily, weekly or out-of-hours. Vetted, insured, uniformed cleaners and low-odour eco products from £25/hr. Serving London, Surrey and the M25.'),
    ('end-of-tenancy-cleaning',  'eot',       'End of Tenancy Cleaning London & Surrey — Fixed Prices from £130',
     'Agency-checklist end of tenancy cleaning with a deposit-back focus. Fixed prices by property size from £130, carpets optional. Tenants, landlords and letting agents across London & Surrey.'),
    ('after-builders-cleaning',  'builders',  'After Builders Cleaning London & Surrey — Fixed Prices from £130',
     'Post-renovation cleaning that removes fine dust, paint splashes and debris with HEPA vacuums. Fixed prices by property size from £130. London, Surrey & the M25.'),
    ('spring-cleaning',          'spring',    'Spring Cleaning & Deep Cleaning London & Surrey from £25/hr',
     'A full seasonal deep clean — inside cupboards, behind appliances, tiles, grout and limescale. Eco-friendly products, from £25/hr (min 4 hours). London, Surrey & the M25.'),
    ('one-off-cleaning',         'oneoff',    'One-Off Deep Cleaning London & Surrey from £25/hr',
     'A single intensive deep clean with no ongoing commitment — before guests, after a busy stretch or for a landlord inspection. From £25/hr, min 4 hours. Book online in 2 minutes.'),
    ('after-party-cleaning',     'party',     'After Party Cleaning London & Surrey from £25/hr',
     'Fast, discreet morning-after cleaning — rubbish, glassware, spills, kitchens and bathrooms reset. From £25/hr, 7 days a week, same-day slots where available. London & Surrey.'),
    ('emergency-cleaning',       'emergency', 'Emergency & Same-Day Cleaning London & Surrey from £30/hr',
     'Urgent same-day cleaning across London, Surrey and the M25 — leaks, spills, last-minute inspections and viewings. From £30/hr with a £120 minimum. Call 07942 369735.'),
]
SLUG_BY_ID = {sid: slug for slug, sid, _, _ in SERVICE_META}
SHORT_NAME = {'domestic': 'Domestic cleaning', 'office': 'Office cleaning', 'eot': 'End of tenancy cleaning',
              'builders': 'After builders cleaning', 'spring': 'Spring cleaning', 'oneoff': 'One-off deep cleaning',
              'party': 'After party cleaning', 'emergency': 'Emergency cleaning'}
PRICE_LINE = {'domestic': 'from £22.50/hr', 'office': 'from £25/hr', 'eot': 'fixed from £130', 'builders': 'fixed from £130',
              'spring': 'from £25/hr', 'oneoff': 'from £25/hr', 'party': 'from £25/hr', 'emergency': 'from £30/hr'}

AREAS = json.load(open('tools/areas.json'))

# ------------------------------------------------------------------ helpers
def esc(s): return html.escape(s, quote=True)
def strip_tags(s): return re.sub(r'<[^>]+>', '', s)

def read(p): return open(p, encoding='utf-8').read()
def write(p, s):
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    open(p, 'w', encoding='utf-8').write(s)

# ------------------------------------------------------------------ 1. images out of index.html
h = read('index.html')
os.makedirs('img', exist_ok=True)
n = 0
def _ext(m):
    global n
    n += 1
    data = base64.b64decode(m.group(2))
    fn = f'img/gallery-{n:02d}.{ "jpg" if m.group(1) in ("jpeg","jpg") else m.group(1)}'
    if not os.path.exists(fn):
        open(fn, 'wb').write(data)
    return '/' + fn
h = re.sub(r'data:image/(\w+);base64,([A-Za-z0-9+/=]{100,})', _ext, h)
print('images extracted:', n)

# ------------------------------------------------------------------ 2. head tags
h = re.sub(r'<title>.*?</title>', '<title>Urban Gleam | Eco-Friendly Cleaners in London, Surrey &amp; the M25</title>', h, count=1)
h = re.sub(r'<meta name="description" content="[^"]*">',
           '<meta name="description" content="Vetted, insured local cleaners for homes and offices across London, Surrey &amp; the M25. Domestic cleaning from £22.50/hr, end of tenancy from £130, eco-friendly products as standard. Book online in 2 minutes.">', h, count=1)

def ld_localbusiness(extra_area=None):
    d = {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "@id": SITE + "/#business",
        "name": BIZ['name'],
        "alternateName": "Urban Gleam Cleaning",
        "description": "Eco-friendly domestic, office, end of tenancy and after-builders cleaning across London, Surrey and the M25.",
        "url": SITE + "/",
        "telephone": BIZ['phone_e164'],
        "email": BIZ['email'],
        "image": SITE + "/img/gallery-01.jpg",
        "logo": SITE + "/favicon-512.png",
        "priceRange": "££",
        "currenciesAccepted": "GBP",
        "paymentAccepted": "Cash, Credit Card, Debit Card, Bank Transfer, PayPal",
        "address": {"@type": "PostalAddress", "streetAddress": BIZ['street'], "addressLocality": BIZ['town'],
                     "addressRegion": BIZ['county'], "postalCode": BIZ['postcode'], "addressCountry": "GB"},
        "geo": {"@type": "GeoCoordinates", "latitude": BIZ['lat'], "longitude": BIZ['lng']},
        "hasMap": BIZ['gbp'],
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "opens": "07:00", "closes": "21:00"}],
        "areaServed": [{"@type": "City", "name": a['name']} for a in AREAS.values()] + [{"@type": "AdministrativeArea", "name": "Greater London"}, {"@type": "AdministrativeArea", "name": "Surrey"}],
        "sameAs": [BIZ['gbp']],
        "knowsAbout": ["Domestic cleaning", "Office cleaning", "End of tenancy cleaning", "After builders cleaning", "Deep cleaning", "Eco-friendly cleaning"],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Cleaning services", "itemListElement": [
            {"@type": "Offer", "itemOffered": {"@type": "Service", "name": SHORT_NAME[sid], "url": f"{SITE}/services/{slug}/"}}
            for slug, sid, _, _ in SERVICE_META]},
    }
    return d

FAQ_ITEMS = re.findall(r'<button class="faq-q">(.*?)<span class="faq-icon">.*?<div class="faq-a"><p>(.*?)</p>', h, flags=re.S)
def ld_faq(items):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": strip_tags(q).strip(), "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a).strip()}}
        for q, a in items]}

def ld_script(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '</script>'

def seo_head(url, title, desc, extra_ld=(), image=SITE + '/img/gallery-01.jpg'):
    return '\n'.join([
        f'<link rel="canonical" href="{url}">',
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        '<meta name="geo.region" content="GB-SRY"><meta name="geo.placename" content="Sunbury-on-Thames">',
        f'<meta name="geo.position" content="{BIZ["lat"]};{BIZ["lng"]}"><meta name="ICBM" content="{BIZ["lat"]}, {BIZ["lng"]}">',
        '<meta property="og:type" content="website"><meta property="og:site_name" content="Urban Gleam">',
        f'<meta property="og:locale" content="en_GB"><meta property="og:url" content="{url}">',
        f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:image" content="{image}"><meta property="og:image:alt" content="Urban Gleam professional cleaning">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{image}">',
    ] + [ld_script(o) for o in extra_ld])

home_ld = [ld_localbusiness(),
           {"@context": "https://schema.org", "@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "Urban Gleam",
            "publisher": {"@id": SITE + "/#business"}, "inLanguage": "en-GB"},
           ld_faq(FAQ_ITEMS)]
h = re.sub(r'<!-- seo:start -->.*?<!-- seo:end -->\n?', '', h, flags=re.S)
h = h.replace('<meta name="theme-color" content="#147A4B">',
              '<meta name="theme-color" content="#147A4B">\n<!-- seo:start -->\n' +
              seo_head(SITE + '/', 'Urban Gleam | Eco-Friendly Cleaners in London, Surrey & the M25',
                       'Vetted, insured local cleaners for homes and offices across London, Surrey & the M25. Domestic cleaning from £22.50/hr, end of tenancy from £130, eco-friendly products as standard.',
                       home_ld) + '\n<!-- seo:end -->', 1)

# ------------------------------------------------------------------ 3. links & copy in index.html
for slug, sid, _, _ in SERVICE_META:
    h = h.replace(f'href="#/service/{sid}"', f'href="/services/{slug}/"')
h = h.replace('<span class="eyebrow" style="margin-bottom:0">Eco-friendly cleaning · London &amp; M25</span>',
              '<span class="eyebrow" style="margin-bottom:0">Professional cleaners · London, Surrey &amp; the M25</span>')
h = h.replace('<p class="hero-sub load-up d1">Vetted local cleaners, <strong>non-toxic biodegradable products</strong> and transparent prices — for homes and offices that gleam without the harsh chemicals.</p>',
              '<p class="hero-sub load-up d1">Vetted local cleaners, <strong>non-toxic biodegradable products</strong> and transparent prices — domestic, office and end of tenancy cleaning for homes and offices across South West London, Surrey and the M25.</p>')
# footer services list: full set with keyword anchors
foot_services = '\n'.join(f'          <li><a href="/services/{slug}/">{SHORT_NAME[sid]}</a></li>' for slug, sid, _, _ in SERVICE_META)
h = re.sub(r'(<h4>Services</h4>\s*<ul>\n).*?(\n\s*</ul>)', lambda m: m.group(1) + foot_services + m.group(2), h, count=1, flags=re.S)
# marquee pills become links
h = h.replace("const pills = AREAS.map(a => '<span class=\"area-pill\">' + a + '</span>').join('');",
              "const pills = AREAS.map(a => '<a class=\"area-pill\" href=\"/areas/' + a.toLowerCase().replace(/ upon thames| on thames/g, '').replace(/[^a-z]+/g, '-') + '/\">' + a + '</a>').join('');")
# static, crawlable area links under the postcode checker
area_links = ' · '.join(f'<a href="/areas/{slug}/">{a["name"]}</a>' for slug, a in AREAS.items())
area_block = ('<!-- area-links:start -->\n    <p class="area-links"><strong>Local cleaners in:</strong> ' + area_links +
              ' — <a href="/areas/">all areas</a></p>\n    <!-- area-links:end -->')
h = re.sub(r'<!-- area-links:start -->.*?<!-- area-links:end -->', '', h, flags=re.S)
h = h.replace('<p id="postcode-result"></p>', '<p id="postcode-result"></p>\n    ' + area_block, 1)
if '.area-links {' not in h:
    h = h.replace('.pc-panel {', '.area-links { max-width: 900px; margin: 34px auto 0; text-align: center; font-size: 13.5px; color: var(--ink-soft); line-height: 2; }\n.area-links a { color: var(--pine-deep); font-weight: 500; }\n.area-links a:hover { text-decoration: underline; }\n.pc-panel {', 1)
# ?svc= deep link from static service pages → booking wizard
if "URLSearchParams(location.search).get('svc')" not in h:
    h = h.replace("  window.addEventListener('hashchange', route);\n  route();",
                  "  window.addEventListener('hashchange', route);\n  route();\n  const qsvc = new URLSearchParams(location.search).get('svc');\n  if (qsvc && SERVICES[qsvc]) selectService(qsvc);", 1)
# service-card 'more' arrows: real pages
h = re.sub(r'(<a class="more-arrow" href=")#/service/([a-z]+)(")', lambda m: m.group(1) + f'/services/{SLUG_BY_ID[m.group(2)]}/' + m.group(3), h)
write('index.html', h)
print('index.html:', len(h), 'bytes')

# ------------------------------------------------------------------ 4. shared CSS
css = re.search(r'<style>\n(.*?)</style>', h, flags=re.S).group(1)
css += '''
/* ---- static SEO pages ---- */
.sp-hero { padding: 140px 0 40px; }
.crumbs { font-size: 12.5px; color: var(--ink-soft); margin-bottom: 18px; letter-spacing: .02em; }
.crumbs a { color: var(--pine-deep); }
.sp-body h2 { font-family: var(--font-body); font-weight: 700; font-size: 1.25rem; margin: 40px 0 18px; }
.sp-body ul.plain { margin: 0 0 18px 20px; color: var(--ink-soft); }
.sp-body ul.plain li { margin-bottom: 6px; }
.svc-list { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.svc-list a { display: flex; justify-content: space-between; gap: 10px; background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 12px 16px; font-size: 14px; transition: .3s var(--ease); }
.svc-list a:hover { border-color: var(--pine); transform: translateY(-2px); }
.svc-list a span { color: var(--pine-deep); font-weight: 600; white-space: nowrap; }
.near-links a { display: inline-block; background: var(--mint); color: var(--moss); border-radius: 999px; padding: 8px 16px; font-size: 13px; font-weight: 500; margin: 0 8px 8px 0; }
.near-links a:hover { background: var(--pine); color: #fff; }
.area-index { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; padding-bottom: 90px; }
.area-index a { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; transition: .3s var(--ease); }
.area-index a:hover { border-color: var(--pine); transform: translateY(-2px); }
.area-index a small { display: block; color: var(--ink-soft); font-size: 12px; margin-top: 2px; }
.review-strip { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 18px; background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 16px 20px; margin: 0 0 26px; font-size: 14px; }
.review-strip .stars { color: var(--gold); letter-spacing: 2px; font-size: 16px; }
.review-strip a { color: var(--pine-deep); font-weight: 600; text-decoration: underline; }
@media (max-width: 760px) { .svc-list { grid-template-columns: 1fr; } .sp-hero { padding-top: 110px; } }
'''
write('assets/site.css', css)

# ------------------------------------------------------------------ 5. static pages
header_html = re.search(r'(<div class="scroll-progress".*?</div>\n\n)<main', h, flags=re.S).group(1)
footer_html = re.search(r'(<!-- ============ FOOTER ============ -->.*?</a>\n)<script>', h, flags=re.S).group(1)
def absolutise(frag):
    frag = re.sub(r'href="#(?!/)([a-z]*)"', lambda m: 'href="/"' if m.group(1) in ('', 'top') else f'href="/#{m.group(1)}"', frag)
    frag = frag.replace('href="#/privacy"', 'href="/#/privacy"').replace('href="#/legal"', 'href="/#/legal"')
    return frag
header_html, footer_html = absolutise(header_html), absolutise(footer_html)

page_js = '''<script>
(function(){
  var header=document.querySelector('.site-header'),bar=document.querySelector('.scroll-progress');
  function onScroll(){header.classList.toggle('scrolled',window.scrollY>20);var h=document.documentElement.scrollHeight-window.innerHeight;bar.style.width=(h>0?(window.scrollY/h)*100:0)+'%';}
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();
  var burger=document.querySelector('.burger'),nav=document.querySelector('.mobile-nav');
  burger.addEventListener('click',function(){burger.classList.toggle('open');nav.classList.toggle('open');document.body.style.overflow=nav.classList.contains('open')?'hidden':'';});
  document.querySelectorAll('.faq-q').forEach(function(btn){btn.addEventListener('click',function(){var item=btn.closest('.faq-item'),a=item.querySelector('.faq-a'),open=item.classList.contains('open');item.parentElement.querySelectorAll('.faq-item.open').forEach(function(o){o.classList.remove('open');o.querySelector('.faq-a').style.maxHeight=null;});if(!open){item.classList.add('open');a.style.maxHeight=a.scrollHeight+'px';}});});
  document.querySelectorAll('.rise,.fade-head,.fade-up').forEach(function(el){el.classList.add('in','vis');});
})();
</script>'''

def shell(url, title, desc, body, ld):
    return f'''<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#147A4B">
{seo_head(url, title, desc, ld)}
</head>
<body>
{header_html}<main id="top">
{body}
</main>
{footer_html}{page_js}
</body>
</html>
'''

def crumbs(items):
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}
    html_ = '<div class="crumbs">' + ' › '.join(f'<a href="{u}">{esc(n)}</a>' if i < len(items) - 1 else esc(n) for i, (n, u) in enumerate(items)) + '</div>'
    return html_, ld

tick = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>'
review_strip = ('<div class="review-strip"><span class="stars">★★★★★</span><span><strong>5-star rated on Google</strong> by our customers</span>'
                f'<a href="{BIZ["gbp"]}" target="_blank" rel="noopener">Read our Google reviews</a></div>')

def price_card(sid, sp):
    fixed = sid in ('eot', 'builders')
    head = ('<div class="from">Fixed prices</div><div class="amt">£130 <small>from</small></div>' if fixed else
            '<div class="from">From</div><div class="amt">£%s <small>/hour</small></div>' % {'domestic': '22.50', 'office': '25.00', 'emergency': '30.00'}.get(sid, '25.00'))
    head += '<div class="from" style="margin-top:6px;text-transform:none;letter-spacing:0">Price for one professional cleaner</div>'
    rows = ''.join(f'<div class="sp-price-row"><span>{r[0]}</span><strong>{r[1]}</strong></div>' for r in sp['rows'])
    wa = 'https://wa.me/447942369735?text=' + html.escape('Hi Urban Gleam, I’d like a quote for ' + SHORT_NAME[sid].lower()).replace(' ', '%20').replace('’', '%E2%80%99')
    return (f'<aside class="sp-price-card"><div class="sp-price-head">{head}</div><div class="sp-price-body">{rows}'
            f'<a class="btn btn-solid" href="/?svc={sid}#book">Book this clean <span class="arr">→</span></a>'
            f'<div class="sp-wa-line">or <a href="{wa}" target="_blank" rel="noopener">ask us on WhatsApp</a> · <a href="tel:{BIZ["phone_e164"]}">{BIZ["phone_display"]}</a></div></div></aside>')

if True:
    s = h.find('  const SERVICE_PAGES = {'); e = h.find('\n  };', s) + 4
    SP = json.loads(subprocess.check_output(['node', '-e', h[s:e] + '\nconsole.log(JSON.stringify(SERVICE_PAGES));']).decode())

service_links = lambda exclude=None: '<div class="svc-list">' + ''.join(
    f'<a href="/services/{slug}/">{SHORT_NAME[sid]}<span>{PRICE_LINE[sid]}</span></a>' for slug, sid, _, _ in SERVICE_META if sid != exclude) + '</div>'
top_areas = ['sunbury-on-thames', 'staines', 'walton-on-thames', 'kingston', 'richmond', 'twickenham', 'wimbledon', 'putney', 'fulham', 'ealing', 'chiswick', 'hounslow']
area_pill_links = lambda slugs: '<div class="near-links">' + ''.join(f'<a href="/areas/{s}/">{AREAS[s]["name"]}</a>' for s in slugs) + '</div>'

urls = [(SITE + '/', '1.0', 'weekly')]

for slug, sid, title, desc in SERVICE_META:
    sp = SP[sid]
    url = f'{SITE}/services/{slug}/'
    name = SHORT_NAME[sid]
    c_html, c_ld = crumbs([('Home', SITE + '/'), ('Services', SITE + '/#services'), (name, url)])
    faqs = sp['faqs']
    svc_ld = {"@context": "https://schema.org", "@type": "Service", "@id": url + '#service', "name": name, "serviceType": name,
              "url": url, "description": desc, "provider": {"@id": SITE + "/#business"},
              "areaServed": [{"@type": "City", "name": a['name']} for a in AREAS.values()],
              "offers": {"@type": "Offer", "priceCurrency": "GBP", "price": {'domestic': '22.50', 'office': '25', 'emergency': '30'}.get(sid, '25') if sid not in ('eot', 'builders') else '130',
                         "priceSpecification": {"@type": "UnitPriceSpecification", "priceCurrency": "GBP",
                                                "price": {'domestic': '22.50', 'office': '25', 'emergency': '30'}.get(sid, '25') if sid not in ('eot', 'builders') else '130',
                                                "unitText": "fixed price from" if sid in ('eot', 'builders') else "per hour"}}}
    body = f'''<section class="sp-hero"><div class="container">
{c_html}
<span class="eyebrow" style="display:flex">{sp['cat']}</span>
<h1>{name} in London, Surrey &amp; the M25</h1>
<p class="sp-tag" style="font-family:var(--font-display);font-weight:800;font-size:1.5rem;color:var(--ink);line-height:1.2;margin-bottom:14px">{sp['h']}</p>
<p class="sp-tag">{sp['tag']}</p>
</div></section>
<div class="container sp-grid">
<div class="sp-body">
{review_strip}
{''.join('<p>' + p + '</p>' for p in sp['intro'])}
<h2>What’s included</h2>
<div class="sp-includes">{''.join(f'<div class="sp-inc">{tick}<span>{i}</span></div>' for i in sp['includes'])}</div>
<h2>Perfect for</h2>
<div class="sp-perfect">{''.join(f'<span>{p}</span>' for p in sp['perfect'])}</div>
<h2>Where we offer {name.lower()}</h2>
<p>Our {name.lower()} team is based in Sunbury-on-Thames and works across South West London, Surrey and everywhere inside the M25 — including:</p>
{area_pill_links(top_areas)}
<p><a href="/areas/">See all {len(AREAS)} areas we cover →</a></p>
<h2>Common questions</h2>
<div class="sp-faq">{''.join(f'<div class="faq-item"><button class="faq-q">{q}<span class="faq-icon">+</span></button><div class="faq-a"><p>{a}</p></div></div>' for q, a in faqs)}</div>
<div class="sp-note">{sp['note']}</div>
<h2>Other cleaning services</h2>
{service_links(sid)}
</div>
{price_card(sid, sp)}
</div>'''
    write(f'services/{slug}/index.html', shell(url, title + ' | Urban Gleam', desc, body, [svc_ld, c_ld, ld_faq(faqs)]))
    urls.append((url, '0.9', 'monthly'))

# areas index
url = SITE + '/areas/'
c_html, c_ld = crumbs([('Home', SITE + '/'), ('Areas we cover', url)])
body = f'''<section class="sp-hero"><div class="container">
{c_html}
<span class="eyebrow" style="display:flex">Coverage</span>
<h1>Local cleaners across London, Surrey &amp; the M25</h1>
<p class="sp-tag">Urban Gleam is based in Sunbury-on-Thames and cleans homes and offices across South West London, Surrey and everywhere inside the M25. Pick your area for local prices and availability, or <a href="/#book" style="color:var(--pine-deep);text-decoration:underline">book online</a> with your postcode.</p>
</div></section>
<div class="container"><div class="area-index">{''.join(f'<a href="/areas/{s}/"><strong>Cleaners in {a["name"]}</strong><small>{a["pc"]}</small></a>' for s, a in AREAS.items())}</div></div>'''
write('areas/index.html', shell(url, 'Areas We Cover — Cleaners in London, Surrey & the M25 | Urban Gleam',
      'Find your local Urban Gleam cleaning team. Domestic, office, end of tenancy and after-builders cleaning across South West London, Surrey and the M25 — from our base in Sunbury-on-Thames.', body, [c_ld]))
urls.append((url, '0.7', 'monthly'))

for slug, a in AREAS.items():
    url = f'{SITE}/areas/{slug}/'
    name = a['name']
    title = f'Cleaners in {name} ({a["pc"]}) — Domestic, Office & End of Tenancy Cleaning'
    desc = (f'Local, vetted and insured cleaners in {name}. Eco-friendly domestic cleaning from £22.50/hr, office cleaning from £25/hr, '
            f'end of tenancy cleaning from £130. Book online in 2 minutes or call 07942 369735.')
    c_html, c_ld = crumbs([('Home', SITE + '/'), ('Areas', SITE + '/areas/'), (name, url)])
    faqs = [
        (f'How much does a cleaner cost in {name}?', f'Regular domestic cleaning in {name} is £22.50 per hour with a £45 minimum visit; one-off and spring cleans are £25 per hour (minimum 4 hours); end of tenancy and after-builders cleans are fixed-price by property size from £130. All prices are for one professional cleaner and include eco-friendly products and equipment.'),
        (f'Do you cover all of {name}?', f'Yes — we cover the whole of {name} ({a["pc"]}) and the surrounding areas. Enter your postcode in the booking form to confirm availability, or call us on 07942 369735.'),
        (f'How quickly can you clean my home in {name}?', 'Regular cleans usually start within a few days. One-off, end of tenancy and emergency cleans can often be arranged within 24–48 hours, and same-day emergency cleaning is available from £30/hr subject to availability.'),
        ('Are your cleaners insured and background-checked?', 'Yes. Every Urban Gleam cleaner is vetted, background-checked, fully insured and trained before their first clean, and regular customers see the same cleaner every visit.'),
    ]
    local_ld = {"@context": "https://schema.org", "@type": "Service", "name": f"Cleaning services in {name}", "serviceType": "Cleaning service",
                "url": url, "provider": {"@id": SITE + "/#business"}, "areaServed": {"@type": "City", "name": name, "containedInPlace": {"@type": "Country", "name": "United Kingdom"}},
                "description": desc}
    body = f'''<section class="sp-hero"><div class="container">
{c_html}
<span class="eyebrow" style="display:flex">Local cleaners · {a['pc']}</span>
<h1>Cleaners in {name} — eco-friendly home, office &amp; end of tenancy <span class="accent">cleaning.</span></h1>
<p class="sp-tag">Vetted, insured local cleaners in {name} using non-toxic, biodegradable products. Transparent prices from £22.50/hr, the same trusted cleaner every visit, and online booking in two minutes.</p>
</div></section>
<div class="container sp-grid">
<div class="sp-body">
{review_strip}
<p>{a['blurb']}</p>
<p>We clean {a['homes']} — from a two-hour weekly tidy to a full agency-standard end of tenancy clean. <strong>Every visit uses non-toxic, biodegradable products</strong> and HEPA-filter vacuums, and every cleaner is vetted, background-checked, insured and trained.</p>
<h2>Cleaning services in {name}</h2>
{service_links()}
<h2>Why {name} customers choose Urban Gleam</h2>
<div class="sp-includes">
<div class="sp-inc">{tick}<span>Local team — based in Sunbury-on-Thames, cleaning {name} every week</span></div>
<div class="sp-inc">{tick}<span>Same trusted cleaner for regular weekly or fortnightly visits</span></div>
<div class="sp-inc">{tick}<span>Eco-friendly, non-toxic products and HEPA vacuums included</span></div>
<div class="sp-inc">{tick}<span>Transparent prices — no deposits, pay after your clean</span></div>
<div class="sp-inc">{tick}<span>Vetted, background-checked and fully insured cleaners</span></div>
<div class="sp-inc">{tick}<span>Open 7am–9pm, 7 days a week, with same-day emergency cleans</span></div>
</div>
<h2>Common questions from {name}</h2>
<div class="sp-faq">{''.join(f'<div class="faq-item"><button class="faq-q">{q}<span class="faq-icon">+</span></button><div class="faq-a"><p>{ans}</p></div></div>' for q, ans in faqs)}</div>
<h2>Nearby areas we also cover</h2>
{area_pill_links(a['near'])}
<p><a href="/areas/">All {len(AREAS)} areas we cover →</a></p>
</div>
<aside class="sp-price-card"><div class="sp-price-head"><div class="from">Cleaners in {name}</div><div class="amt">£22.50 <small>/hour</small></div><div class="from" style="margin-top:6px;text-transform:none;letter-spacing:0">Domestic cleaning · one professional cleaner</div></div>
<div class="sp-price-body">
<div class="sp-price-row"><span>Domestic cleaning</span><strong>£22.50/hr · min £45</strong></div>
<div class="sp-price-row"><span>Office cleaning</span><strong>£25/hr · min £50</strong></div>
<div class="sp-price-row"><span>Spring / one-off deep clean</span><strong>£25/hr · min 4 hrs</strong></div>
<div class="sp-price-row"><span>End of tenancy</span><strong>Fixed from £130</strong></div>
<div class="sp-price-row"><span>After builders</span><strong>Fixed from £130</strong></div>
<div class="sp-price-row"><span>Emergency / same-day</span><strong>£30/hr · min £120</strong></div>
<a class="btn btn-solid" href="/#book">Book a clean in {name.split(' ')[0]} <span class="arr">→</span></a>
<div class="sp-wa-line">or <a href="https://wa.me/447942369735?text=Hi%20Urban%20Gleam%2C%20I%27d%20like%20a%20cleaning%20quote%20in%20{name.replace(' ', '%20')}" target="_blank" rel="noopener">ask us on WhatsApp</a> · <a href="tel:{BIZ['phone_e164']}">{BIZ['phone_display']}</a></div>
</div></aside>
</div>'''
    write(f'areas/{slug}/index.html', shell(url, title + ' | Urban Gleam', desc, body, [local_ld, c_ld, ld_faq(faqs)]))
    urls.append((url, '0.8', 'monthly'))

# ------------------------------------------------------------------ 6. sitemap + robots
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u, p, f in urls:
    sm.append(f'  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>{f}</changefreq><priority>{p}</priority></url>')
sm.append('</urlset>\n')
write('sitemap.xml', '\n'.join(sm))
write('robots.txt', f'User-agent: *\nAllow: /\nDisallow: /tools/\n\nSitemap: {SITE}/sitemap.xml\n')
print('pages:', len(urls))
