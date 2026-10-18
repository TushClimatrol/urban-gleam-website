# Guide pages (/guides/<slug>/). Plain, useful articles that answer the questions people type into Google before
# they book a cleaner. Edit here, then run: python3 tools/build-seo.py
#
# Each guide: slug, title (<title> and H1), desc (search description), published (first publish date, never changes),
# summary (one paragraph under the H1), sections (list of blocks), faqs, cta (service id for the price card).
# Blocks: ('h2', text) · ('p', html) · ('ul', [items]) · ('check', [items]) · ('table', [header], [rows]) · ('tip', html)
# {price:xxx} placeholders are filled from the live price config in index.html by build-seo.py.

GUIDES = [
    {
        'slug': 'cleaning-prices-london-surrey',
        'title': 'Cleaning Prices in London & Surrey: 2026 Guide',
        'h1': 'How much does cleaning cost in London &amp; Surrey? <span class="accent-g">2026 prices.</span>',
        'desc': 'Hourly cleaner rates, end of tenancy, after builders, oven and carpet cleaning prices in London & Surrey for 2026 — what affects the price and how to compare quotes.',
        'published': '2026-10-18',
        'cta': 'domestic',
        'summary': 'Cleaning prices in the UK are quoted three ways: by the hour, as a fixed price by property size, or per item. '
                   'This guide explains what each costs around Sunbury-on-Thames, Surrey and South West London in 2026, what pushes a price up or down, '
                   'and the questions worth asking before you book. Our own prices are shown alongside so you can compare.',
        'sections': [
            ('h2', 'Hourly cleaning rates'),
            ('p', 'Regular domestic cleaning is almost always priced per hour, per cleaner. Across Surrey and outer South West London, independent cleaners '
                  'typically charge <strong>£15–£20 an hour</strong> (directory listings for Sunbury-on-Thames show £17–£23), while insured cleaning companies that '
                  'supply products, equipment and a replacement if your cleaner is ill charge <strong>£20–£30 an hour</strong>. Inner London rates run a few pounds higher.'),
            ('table', ['Service', 'Typical company rate', 'Urban Gleam'], [
                ['Domestic cleaning (regular)', '£20–£28/hr', '{price:domestic}/hr, minimum {min:domestic}'],
                ['Office cleaning', '£22–£32/hr', '{price:office}/hr, minimum {min:office}'],
                ['Spring / deep clean', '£25–£35/hr', '{price:spring}/hr, minimum 4 hours'],
                ['One-off clean', '£25–£35/hr', '{price:oneoff}/hr, minimum 4 hours'],
                ['Communal areas (flats)', '£22–£30/hr', '{price:communal}/hr, minimum {min:communal}'],
                ['Emergency / same-day', '£30–£45/hr', '{price:emergency}/hr, minimum {min:emergency}'],
            ]),
            ('p', 'A useful rule of thumb for a regular clean is <strong>one hour per bedroom plus one hour</strong>: a two-bedroom flat takes about three hours, '
                  'a four-bedroom house about five. The first visit usually runs longer because it is really a light deep clean.'),
            ('h2', 'End of tenancy cleaning prices'),
            ('p', 'End of tenancy cleaning is normally a <strong>fixed price by property size</strong>, because the job is defined by the letting agent’s checklist rather '
                  'than by time. Expect to pay roughly £120–£180 for a studio, £150–£220 for a one-bed, £200–£300 for a two-bed and £300–£450 for a three-bed house in Surrey '
                  'and outer London, with professional carpet cleaning adding £40–£100 depending on the number of rooms.'),
            ('table', ['Property', 'Typical range', 'Urban Gleam (without / with carpets)'], [
                ['Studio flat', '£120–£180', '{eot:studio}'],
                ['One bedroom', '£150–£220', '{eot:1}'],
                ['Two bedroom', '£200–£300', '{eot:2}'],
                ['Three bedroom', '£300–£450', '{eot:3}'],
                ['Four+ bedroom', 'Quoted individually', 'Quoted individually'],
            ]),
            ('tip', 'Cleaning is consistently the most common reason tenancy deposits are disputed in the UK. A fixed-price professional clean with a receipt is '
                    'the simplest way to protect a deposit that is usually five weeks’ rent. See our <a href="/guides/end-of-tenancy-cleaning-checklist/">end of tenancy cleaning checklist</a>.'),
            ('h2', 'After builders cleaning prices'),
            ('p', 'After builders (post-renovation) cleaning is priced like end of tenancy cleaning — by property size — but quotes vary more because the amount of fine dust, '
                  'paint and adhesive residue differs so much from job to job. In the UK, a full after builders clean typically costs <strong>£150–£500</strong> for a house, '
                  'or around <strong>£25–£40 an hour per cleaner</strong> where it is quoted hourly. Ask whether the price includes inside cupboards, window frames and '
                  'light fittings, and whether a second “settle dust” visit a few days later is included or extra.'),
            ('p', 'Our after builders prices are the same fixed prices as end of tenancy cleaning: from {price_from:builders} for a studio. '
                  'Full details on our <a href="/services/after-builders-cleaning/">after builders cleaning</a> page.'),
            ('h2', 'Oven, carpet and window cleaning prices'),
            ('p', 'Specialist cleans are priced per item rather than by time:'),
            ('ul', [
                '<strong>Oven cleaning:</strong> £45–£70 for a single oven, £65–£95 for a double, £85–£130 for a range cooker. Urban Gleam: single {opt:oven:single}, double {opt:oven:double}, range {opt:oven:range}.',
                '<strong>Carpet cleaning:</strong> £20–£40 per room with a minimum call-out of £50–£80; a three-piece suite £60–£120. Urban Gleam: {opt:carpet:r1} for one room, {opt:carpet:r3} for three, sofas from {opt:carpet:sofa}.',
                '<strong>Window cleaning:</strong> £10–£20 for a flat or small terraced house outside, £20–£40 for a semi or detached house, with inside glass adding roughly 50%. Urban Gleam: from {opt:window:flat}.',
            ]),
            ('h2', 'What changes the price'),
            ('ul', [
                '<strong>Condition.</strong> A home that is cleaned regularly costs less per visit than one that has not been cleaned for months; heavy limescale, grease or mould adds time.',
                '<strong>Products and equipment.</strong> Some cleaners expect you to provide them; companies usually include them. Eco-friendly products no longer carry a premium with most firms, including ours.',
                '<strong>Frequency.</strong> Weekly and fortnightly cleans are often cheaper per hour than one-offs, and many companies have a longer minimum for one-off and deep cleans.',
                '<strong>Access and parking.</strong> Controlled parking zones in London boroughs and no on-site parking can add a parking charge; Spelthorne and most of Surrey rarely do.',
                '<strong>Insurance and vetting.</strong> Public liability insurance, DBS checks and a replacement cleaner when yours is ill are what you pay for above the independent-cleaner rate.',
                '<strong>Extras.</strong> Inside the oven, inside the fridge, interior windows, ironing and balconies are usually priced as add-ons of £15–£30 each.',
            ]),
            ('h2', 'How to compare quotes'),
            ('ul', [
                'Ask whether the price is <strong>per cleaner</strong> — two cleaners for two hours is four cleaning hours, not two.',
                'Check that <strong>products and equipment are included</strong>, and that the vacuum has a HEPA filter if anyone in the house has allergies.',
                'For end of tenancy, ask for a <strong>fixed price and a written list</strong> of what is included, and whether they will return free of charge if the agent raises an issue.',
                'Ask about the <strong>minimum charge</strong> and whether there is a deposit. (We have no deposit — you pay after the clean.)',
                'Look for recent <strong>Google reviews with photos</strong>; the best evidence of a good clean is a before-and-after picture.',
            ]),
        ],
        'faqs': [
            ('How much does a cleaner cost per hour in the UK in 2026?', 'Independent cleaners typically charge £15–£20 an hour and insured cleaning companies £20–£30 an hour, with London at the top of each range. Urban Gleam charges {price:domestic} an hour for regular domestic cleaning, with products and equipment included.'),
            ('How much is an end of tenancy clean?', 'Usually a fixed price by property size: roughly £120–£180 for a studio, £150–£220 for a one-bed, £200–£300 for a two-bed and £300–£450 for a three-bed house, plus £40–£100 for carpets. Urban Gleam charges from {price_from:eot}.'),
            ('Is it cheaper to pay a cleaner hourly or a fixed price?', 'For regular cleaning, hourly is cheaper and more flexible. For one-off jobs with a defined finish — end of tenancy, after builders, oven cleaning — a fixed price protects you if the job takes longer than expected.'),
            ('Do I need to provide cleaning products?', 'With most independent cleaners, yes. With cleaning companies, including Urban Gleam, products and equipment are included in the price.'),
        ],
    },
    {
        'slug': 'end-of-tenancy-cleaning-checklist',
        'title': 'End of Tenancy Cleaning Checklist (Agent-Approved)',
        'h1': 'End of tenancy cleaning checklist: what letting agents <span class="accent-g">actually check.</span>',
        'desc': 'Room-by-room end of tenancy cleaning checklist based on what UK letting agents inspect at check-out, plus how to protect your deposit.',
        'published': '2026-10-18',
        'cta': 'eot',
        'summary': 'At check-out, the agent or inventory clerk compares the property with the check-in inventory, room by room. Cleaning is the most common reason deposits '
                   'are disputed, so this is the list our end of tenancy teams work to — the same things the clerk looks for. Use it to clean yourself, '
                   'or to check a professional clean before you hand the keys back.',
        'sections': [
            ('h2', 'Before you start'),
            ('ul', [
                'Dig out the <strong>check-in inventory</strong> and photos. The standard you need is “as clean as at check-in, allowing for fair wear and tear” — not showroom-new.',
                'Book the clean for <strong>after the removal van has gone</strong> and before the check-out appointment, ideally with a day in between for anything that needs a second pass.',
                'Return everything to where the inventory says it was, and replace any blown bulbs — missing bulbs are one of the most frequent small deductions.',
                'If the tenancy agreement says the carpets must be professionally cleaned, keep the receipt: the clerk may ask for it.',
            ]),
            ('h2', 'Kitchen'),
            ('check', [
                'Oven cleaned inside and out, including racks, trays, the door glass and the seal — this is the first thing every clerk opens',
                'Hob, rings, pan supports and the splashback degreased',
                'Extractor hood cleaned and the filters degreased or replaced',
                'Fridge and freezer defrosted, emptied, cleaned and left switched off with the doors propped open',
                'Washing machine drawer, seal and filter cleaned; dishwasher filter and seals cleaned',
                'Microwave inside and out',
                'All cupboards and drawers emptied and wiped inside, tops of wall units dusted',
                'Worktops, tiles and grout cleaned; sink and taps descaled and polished',
                'Bin cleaned inside and out; floor swept, mopped and the edges and corners done',
            ]),
            ('h2', 'Bathrooms'),
            ('check', [
                'Limescale removed from taps, shower head, shower screen and tiles',
                'Grout and silicone cleaned; mould treated',
                'Toilet cleaned inside, outside, behind and under the seat hinges',
                'Bath, basin and shower tray cleaned and polished; plugholes cleared of hair',
                'Mirrors, glass and chrome polished streak-free',
                'Extractor fan cover dusted; cabinet cleaned inside and out',
                'Floor cleaned including behind the toilet and the door',
            ]),
            ('h2', 'Bedrooms and living rooms'),
            ('check', [
                'Inside wardrobes, drawers and cupboards wiped and left empty',
                'Skirting boards, door frames, doors and door handles wiped',
                'Light switches, sockets and light fittings dusted and cleaned',
                'Radiators cleaned front, top and (as far as possible) behind',
                'Curtain rails, blinds and window sills dusted; blinds wiped slat by slat',
                'Windows cleaned inside, including frames and the tracks of sliding windows',
                'Mattresses vacuumed; under beds and behind furniture vacuumed',
                'Marks on walls removed where possible (sugar soap works on most scuffs)',
                'Carpets vacuumed thoroughly, then professionally cleaned if the tenancy agreement requires it or there are stains',
            ]),
            ('h2', 'Hallway, stairs and the bits people forget'),
            ('check', [
                'Stairs, banisters and spindles dusted; stair carpet edges vacuumed',
                'Front door inside and out, letterbox and door furniture',
                'Cobwebs from ceiling corners and light fittings in every room',
                'Loft hatch, meter cupboard and under-stairs cupboard emptied and wiped',
                'Balcony, patio or garden tidied, swept and cleared of rubbish and cigarette ends',
                'Bins emptied, washed and put out or returned to their place',
                'All rubbish, food and personal items removed from the property',
            ]),
            ('h2', 'Protecting your deposit'),
            ('p', 'Your deposit must be held in one of the government-approved tenancy deposit schemes, and if you disagree with a deduction you can use the scheme’s free '
                  'dispute service. The adjudicator decides on evidence, so:'),
            ('ul', [
                'Take <strong>dated photos of every room</strong> after cleaning, including inside the oven, fridge and cupboards.',
                'Keep the <strong>cleaning receipt</strong> if you used a company — it is strong evidence that the property was professionally cleaned.',
                'Attend the <strong>check-out inspection</strong> if you can, and ask the clerk to note anything you disagree with on the report.',
                'Remember the standard is <strong>“as at check-in”</strong>. A landlord cannot charge you to improve on the condition you received the property in.',
            ]),
            ('h2', 'DIY or professional?'),
            ('p', 'A thorough end of tenancy clean of a two-bedroom flat takes two people most of a day, plus the cost of hiring a carpet cleaner and buying oven cleaner, '
                  'descaler and degreaser. Against that, a professional clean costs a fixed price from {price_from:eot} (see our '
                  '<a href="/guides/cleaning-prices-london-surrey/">guide to cleaning prices</a>), comes with the receipt agents like to see, and we come back free of charge '
                  'if the agent raises anything within 24 hours. If your deposit is five weeks’ rent, the maths usually favours booking it.'),
        ],
        'faqs': [
            ('How clean does a rented property need to be at check-out?', 'As clean as it was at check-in, allowing for fair wear and tear. The check-in inventory and photos are the benchmark the clerk uses, so get hold of them before you start.'),
            ('Do I have to pay for professional cleaning when I move out?', 'A landlord cannot force you to use a professional cleaner — only to return the property to its check-in standard of cleanliness. Many tenancy agreements do, however, require professionally cleaned carpets, and you may need the receipt.'),
            ('What do letting agents check first?', 'The oven, the inside of the fridge, bathroom limescale and the inside of cupboards — the places tenants most often skip and the easiest for an inventory clerk to spot.'),
            ('How long does an end of tenancy clean take?', 'A professional team of two typically takes 3–4 hours for a one-bedroom flat and 5–7 hours for a three-bedroom house, longer if carpets are being cleaned too.'),
        ],
    },
]
