#!/usr/bin/env python3
"""CHEST 2026 conference site generator - Maverix design system.

Reads config.json + physicians.json, writes every page, the service worker and
the manifest. Styling lives in theme.css (design-system tokens) and pages.css
(components); neither is inlined, so nine pages share two cached stylesheets.

Deliberate deviations from the design system are commented at the point of use
and listed in BRAND-NOTES.md. To reskin for another conference, edit
config.json and rerun - the slug drives filenames, nav, storage keys and the
service worker precache list.
"""
import json, html, os, re, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
def rd(p):
    with open(os.path.join(HERE, p), encoding='utf-8') as f: return f.read()
def wr(p, s):
    with open(os.path.join(HERE, p), 'w', encoding='utf-8') as f: f.write(s)
    return len(s)

CFG  = json.loads(rd('config.json'))
PHYS = json.loads(rd('physicians.json'))
SLUG = CFG['slug']
E    = html.escape

PAGES = [
    ('index',     'Home',        'index.html'),
    ('targets',   'Target list', f'{SLUG}.html'),
    ('coverage',  'Coverage',    f'{SLUG}-coverage.html'),
    ('leaders',   'Leaderboard', f'{SLUG}-leaders.html'),
    ('staffing',  'Calendar',    f'{SLUG}-staffing.html'),
    ('happyhour', 'Happy hour',  f'{SLUG}-happyhour.html'),
    ('tips',      'Cryo tips',   f'{SLUG}-tips.html'),
    ('invites',   'Invites',     f'{SLUG}-invites.html'),
    ('info',      'Event info',  f'{SLUG}-info.html'),
]
FILE = {k: f for k, _, f in PAGES}
# Flat at the repo root: GitHub's web uploader does not preserve subfolder paths
# for individually selected files, and this repo is populated through that UI.
FONTS = ['poppins-latin-300-normal.woff2', 'poppins-latin-300-italic.woff2',
         'poppins-latin-400-normal.woff2', 'poppins-latin-400-italic.woff2',
         'poppins-latin-500-normal.woff2', 'poppins-latin-600-normal.woff2',
         'poppins-latin-700-normal.woff2']

# The double-chevron in a circle is the entire icon system (rule 10).
CHEVRON = ('<span class="mvx-circ"><svg width="13" height="13" viewBox="0 0 24 24" aria-hidden="true">'
           '<polyline points="5 4 13 12 5 20"/><polyline points="13 4 21 12 13 20"/></svg></span>')

def header(active):
    CUR = ' aria-current="page"'
    links = ''.join(
        '<a href="%s"%s>%s</a>' % (fn, CUR if k == active else '', E(label))
        for k, label, fn in PAGES)
    return (f'<header class="mvx-header"><div class="mvx-headinner">'
            f'<div class="mvx-brand">maverix<span>.</span></div>'
            f'<nav class="nav">{links}</nav></div></header>')

def head(title, extra_css=''):
    css = f'<style>{extra_css}</style>' if extra_css else ''
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="{CFG['theme']}">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="{E(CFG['app_short_name'])}">
<link rel="apple-touch-icon" href="apple-touch-icon.png?v=3">
<link rel="icon" type="image/png" href="favicon.png?v=3" sizes="32x32">
<link rel="stylesheet" href="theme.css">
<link rel="stylesheet" href="pages.css">
<title>{E(title)}</title>{css}</head><body>
"""

SW_REG = ("<script>if('serviceWorker' in navigator){window.addEventListener('load',"
          "function(){navigator.serviceWorker.register('sw.js').catch(function(){});});}</script>")
FOOT = SW_REG + "\n</body></html>\n"

def shell(active, title, body, wide=False, extra_css=''):
    w = ' wide' if wide else ''
    return (head(title, extra_css) + header(active) +
            f'<main class="mvx-container{w}">' + body + '</main>' + FOOT)

def reslug(s):
    """Rewrite recovered AABIP assets onto this slug.

    localStorage is scoped per ORIGIN, not per path, so every project site under
    one github.io account shares a bucket. A key missed here would let this site
    read and flush the previous conference's queue.
    """
    s = s.replace('aabip-leads', f'{SLUG}-leads')
    s = re.sub(r'\baabip\.(state|queue|synced|rep|warmed|leaders)\b', rf'{SLUG}.\1', s)
    for old, key in [('aabip-leaders.html', 'leaders'), ('aabip-staffing.html', 'staffing'),
                     ('aabip-dinner.html', 'happyhour'), ('aabip-panel.html', 'happyhour'),
                     ('aabip-tips.html', 'tips'), ('aabip-invites.html', 'invites'),
                     ('aabip-info.html', 'info'), ('aabip-coverage.html', 'coverage'),
                     ('aabip.html', 'targets')]:
        s = s.replace(old, FILE[key])
    return s

def src(name):
    return reslug(rd(os.path.join('_build', name)))

ENDPOINT_OLD = ('https://script.google.com/macros/s/AKfycbwifm_Qo5wHgnbh6Rss6a'
                'yMYmvhIM8LvibHm9DSzOS4v0qs3SFPHHsIp5wPoQ4zqbw5Mw/exec')
def wire(js):
    return js.replace(ENDPOINT_OLD, CFG['sync_endpoint'])

DRAFT = ('<div class="mvx-notice"><strong>Draft</strong> &mdash; physician records are carried over '
         f'from AABIP 2026 as placeholders, re-numbered {SLUG}-1&hellip;{SLUG}-{len(PHYS)}. '
         'They are <em>not</em> the CHEST target list. Ranks, talk tracks and territories '
         'change when the real list lands.</div>')

# With a placeholder endpoint the sync layer fails quietly and a rep testing the
# prototype reasonably concludes the checkboxes are broken. Say so on the page.
WIRED = CFG['sync_endpoint'].startswith('https://')
NOSYNC = ('' if WIRED else
          '<div class="mvx-notice"><strong>Prototype</strong> &mdash; the sync backend is not '
          'connected yet, so checkboxes will not save or appear on anyone else\'s device. '
          'Everything else works. Marks made now are lost on reload.</div>')

# ------------------------------------------------------------------ target list
def render_targets():
    territories = sorted({p['ter'] for p in PHYS if p['ter']})
    topts = ''.join(f'<option value="{E(t)}">{E(t)}</option>' for t in territories)
    cards = []
    for p in sorted(PHYS, key=lambda x: x['r']):
        pid = E(p['id'])
        photo = (f'<img src="{E(p["photo"])}" alt="{E(p["name"])}" referrerpolicy="no-referrer" '
                 f'loading="lazy" onerror="this.style.display=&#39;none&#39;">') if p.get('photo') else ''
        badges = [f'<span class="vol">{E(p["vol"])}</span>']
        if p.get('tier'): badges.append(f'<span class="tier t{E(p["tier"])}">Tier {E(p["tier"])}</span>')
        if p.get('cryo') == '1': badges.append('<span class="cryo">Cryo Target</span>')
        links = []
        if p.get('hp'):     links.append(f'<a href="{E(p["hp"])}" target="_blank">Hospital page &#8599;</a>')
        if p.get('acuity'): links.append(f'<a href="{E(p["acuity"])}" target="_blank">AcuityMD &#8599;</a>')
        if p.get('photo'):  links.append(f'<a href="{E(p["photo"])}" target="_blank">Photo &#8599;</a>')
        contact = (f'<a href="mailto:{E(p["email"])}">{E(p["email"])}</a>' if p.get('email')
                   else '<span style="color:var(--text-muted)">no email</span>')
        if p.get('phone'): contact += f'<span style="color:var(--border-strong)">&middot;</span><span style="color:var(--text-muted)">{E(p["phone"])}</span>'
        contact += f'<span class="territory-tag">{E(p["ter"])}</span>'
        talk = (f'<div class="talk"><span class="talk-label">Talk track</span>{E(p["talk"])}</div>'
                if p.get('talk') else '')
        ctx = (f'<div class="ctx"><span class="ctx-label">Context</span>{E(p["ctx"])}</div>'
               if p.get('ctx') else '')
        cards.append(f"""<article class="card" id="{pid}" data-id="{pid}" data-territory="{E(p['ter'])}" data-tier="{E(p.get('tier',''))}" data-cryo="{E(p.get('cryo','0'))}" data-demo="{E(p.get('demo','0'))}" data-rank="{p['r']}" data-surname="{E(p.get('surname',''))}">
  <div class="row">
    <div class="photo">{photo}</div>
    <div class="body">
      <div class="rank">#{p['r']:02d} &middot; {E(p['st'])}</div>
      <div class="name">{E(p['name'])}<span class="checkmark" aria-label="Connected">&#10003;</span></div>
      <div class="inst">{E(p['inst'])}</div>
      <div class="badges">{''.join(badges)}</div>
      <div class="meta">NPI {E(p.get('npi',''))}</div>
      <div class="links">{''.join(links)}</div>
      <div class="contact">{contact}</div>
    </div>
  </div>
  <div class="actions"><label class="actbox conf"><input type="checkbox" class="conf-cb"><span>Connected at conference</span></label><label class="actbox emailed"><input type="checkbox" class="email-cb"><span>Emailed</span></label><button type="button" class="actbox cap capbtn">Badge photo + note<span class="capcount"></span></button></div>
  {talk}
  {ctx}
</article>""")
    body = f"""<span class="mvx-eyebrow">{E(CFG['conference'])} &middot; {E(CFG['city'])}</span>
<h1>Target list</h1>
<div class="sub">{len(PHYS)} {E(CFG['specialty'].lower())} ranked by estimated annual core procedure volume. Mark a physician after speaking with or emailing them &mdash; status syncs across every device.</div>
{NOSYNC}{DRAFT}
<div class="filter-bar">
  <label>Territory <select id="territory-filter"><option value="">All</option>{topts}</select></label>
  <label>Tier <select id="tier-filter"><option value="">All</option><option value="1">Tier 1</option><option value="2">Tier 2</option></select></label>
  <label>Tag <select id="tag-filter"><option value="">All</option><option value="cryo">Cryo target</option></select></label>
  <label>Sort <select id="sort-order"><option value="rank">By rank</option><option value="name">A&ndash;Z</option></select></label>
  <span class="cnt" id="card-count"></span>
</div>
<div class="grid">{''.join(cards)}</div>
<div class="syncpill" id="syncpill">&nbsp;</div>
<p class="mvx-rxnote">All devices are prescription-only, for use by trained physicians. See each product's Instructions for Use for complete indications, contraindications, warnings, and precautions.</p>
<script>{src('_script0.js')}</script>
<script>{wire(src('_script1.js'))}</script>"""
    return shell('targets', f"{CFG['conference']} - Target list", body, wide=True)

# ------------------------------------------------------------------ coverage
def render_coverage():
    on_site = {r['territory'] for r in CFG['reps'] if r['territory']}
    ters = sorted({p['ter'] for p in PHYS if p['ter']})
    rows_t = []
    for t in ters:
        n = sum(1 for p in PHYS if p['ter'] == t)
        flag = '' if t in on_site else '<span class="norep">no rep on site</span>'
        rows_t.append(f'<tr data-ter="{E(t)}"><td data-l="Territory">{E(t)}{flag}</td>'
                      f'<td data-l="Total">{n}</td><td data-l="Connected" class="c">0</td>'
                      f'<td data-l="Emailed" class="e">0</td><td data-l="Untouched" class="u">{n}</td>'
                      f'<td data-l="Covered"><div class="bar"><i style="width:0%"></i></div></td></tr>')
    rows_p = ''.join(
        f'<tr data-id="{E(p["id"])}" data-ter="{E(p["ter"])}">'
        f'<td data-l="Rank">{p["r"]}</td>'
        f'<td data-l="Name" class="nm"><a href="{FILE["targets"]}#{E(p["id"])}">{E(p["name"])}</a></td>'
        f'<td data-l="Institution">{E(p["inst"])}</td>'
        f'<td data-l="Territory">{E(p["ter"])}</td>'
        f'<td data-l="Conf"><input type="checkbox" class="conf-cb"></td>'
        f'<td data-l="Emailed"><input type="checkbox" class="email-cb"></td></tr>'
        for p in sorted(PHYS, key=lambda x: x['r']))
    js = """(function(){
var ENDPOINT='%s',LS_STATE='%s.state';
function get(k,d){try{var v=JSON.parse(localStorage.getItem(k));return v==null?d:v;}catch(e){return d;}}
var state=get(LS_STATE,{});
var prows=[].slice.call(document.querySelectorAll('tbody#pbody tr'));
function pct(a,b){return b?Math.round(a/b*100):0;}
function render(){
  var tot=prows.length,c=0,e=0,per={};
  prows.forEach(function(r){
    var id=r.dataset.id,t=r.dataset.ter;
    per[t]=per[t]||{n:0,c:0,e:0};per[t].n++;
    var cf=!!state[id+'-conf'],em=!!state[id+'-email'];
    if(cf){c++;per[t].c++;} if(em){e++;per[t].e++;}
    r.querySelector('.conf-cb').checked=cf; r.querySelector('.email-cb').checked=em;});
  document.getElementById('s-tot').textContent=tot;
  document.getElementById('s-con').textContent=c;
  document.getElementById('s-ema').textContent=e;
  document.getElementById('s-unt').textContent=tot-c;
  document.getElementById('p-con').textContent=pct(c,tot)+'%%';
  document.getElementById('p-ema').textContent=pct(e,tot)+'%%';
  document.getElementById('p-unt').textContent=pct(tot-c,tot)+'%%';
  [].slice.call(document.querySelectorAll('tbody#tbody tr')).forEach(function(r){
    var d=per[r.dataset.ter]||{n:0,c:0,e:0};
    r.querySelector('.c').textContent=d.c; r.querySelector('.e').textContent=d.e;
    r.querySelector('.u').textContent=d.n-d.c;
    r.querySelector('.bar>i').style.width=pct(d.c,d.n)+'%%';});}
function pull(){
  if(!/^https:/.test(ENDPOINT))return;             // endpoint not wired yet
  fetch(ENDPOINT).then(function(r){return r.json();}).then(function(j){
    if(j&&j.state){state=j.state;try{localStorage.setItem(LS_STATE,JSON.stringify(state));}catch(e){}render();}
  }).catch(function(){});}
render();pull();setInterval(pull,6000);})();""" % (CFG['sync_endpoint'], SLUG)
    body = f"""<span class="mvx-eyebrow">{E(CFG['conference'])}</span>
<h1>Coverage</h1>
<div class="sub">Who has been reached, and which territories still need attention. Reads the same sheet as the target list and refreshes every six seconds.</div>
{NOSYNC}{DRAFT}
<div class="mvx-statgrid">
  <div class="mvx-statcell"><div class="n" id="s-tot">0</div><div class="l">Physicians</div></div>
  <div class="mvx-statcell"><div class="n" id="s-con">0</div><div class="l">Connected</div><div class="p" id="p-con">0%</div></div>
  <div class="mvx-statcell"><div class="n" id="s-ema">0</div><div class="l">Emailed</div><div class="p" id="p-ema">0%</div></div>
  <div class="mvx-statcell"><div class="n" id="s-unt">0</div><div class="l">Not yet reached</div><div class="p" id="p-unt">0%</div></div>
</div>
<div class="mvx-seclabel">By territory</div>
<table class="covtable"><thead><tr><th>Territory</th><th>Total</th><th>Connected</th><th>Emailed</th><th>Untouched</th><th>% covered</th></tr></thead><tbody id="tbody">{''.join(rows_t)}</tbody></table>
<div class="mvx-seclabel">By physician</div>
<table class="covtable"><thead><tr><th>Rank</th><th>Name</th><th>Institution</th><th>Territory</th><th>Conf</th><th>Email</th></tr></thead><tbody id="pbody">{rows_p}</tbody></table>
<script>{js}</script>"""
    return shell('coverage', f"{CFG['conference']} - Coverage", body, wide=True)

# ------------------------------------------------------------------ staffing
def render_staffing():
    reps = [r['name'] for r in CFG['reps']]
    demo_n = CFG['demo_room']['staff_per_block']
    dr = CFG['demo_room']
    out, rot = [], 0
    for d in CFG['days']:
        if d['kind'] == 'setup':
            crew = ' &middot; '.join(E(x) for x in d['crew'])
            out.append(f"""<div class="daycard"><h2>{E(d['label'])} &mdash; Setup</h2>
<div class="daymeta">{E(d['note'])}</div>
<div class="crewline"><strong>Setup crew, {E(d['window'])}:</strong> {crew} <span style="color:var(--text-muted)">({E(d['crew_note'])})</span></div></div>""")
            continue
        rows = []
        half = len(reps) // 2
        for bi, b in enumerate(d['blocks']):
            order = reps[rot % len(reps):] + reps[:rot % len(reps)]
            on = order[bi * half:(bi + 1) * half]
            demo, booth = on[:demo_n], on[demo_n:]
            chips = (''.join(f'<span>{E(x)}</span>' for x in booth) +
                     ''.join(f'<span class="demo">{E(x)} &middot; demo</span>' for x in demo))
            rows.append(f'<tr><td class="blk">{E(b["from"])}&ndash;{E(b["to"])}</td>'
                        f'<td><div class="who">{chips}</div></td>'
                        f'<td>{len(booth)} at booth {E(CFG["booth"])}, {len(demo)} in demo room</td></tr>')
        rot += 4
        ev = ''.join(f'<div class="crewline"><strong>{E(x["title"])}:</strong> {E(x["time"])} &middot; {E(x["where"])}</div>'
                     for x in d.get('events', []))
        td = d.get('teardown')
        if td:
            ev += (f'<div class="crewline"><strong>Teardown, {E(td["window"])}:</strong> '
                   + ' &middot; '.join(E(x) for x in td['crew'])
                   + f' <span style="color:var(--text-muted)">({E(td["crew_note"])})</span></div>')
        drtxt = (f'{E(dr["name"])} {E(dr["number"])}' if dr['number'] != 'TBA'
                 else f'{E(dr["name"])} <span class="tba">room TBA</span>')
        out.append(f"""<div class="daycard"><h2>{E(d['label'])}</h2>
<div class="daymeta">Exhibit hall {E(d['hall_open'])}&ndash;{E(d['hall_close'])} MT &middot; {drtxt}</div>
<table class="shiftgrid"><tr><th>Block</th><th>On duty</th><th>Split</th></tr>{''.join(rows)}</table>{ev}</div>""")
    body = f"""<span class="mvx-eyebrow">Booth {E(CFG['booth'])} &middot; {E(CFG['city'])}</span>
<h1>Booth calendar</h1>
<div class="sub">{E(CFG['dates'])}. Two blocks a day, rotating so nobody draws the same block twice.</div>
<div class="mvx-notice"><strong>Draft rotation</strong> &mdash; {len(reps)} reps split evenly across two blocks a day. Swap names freely; only the block times are fixed by hall hours.</div>
{''.join(out)}"""
    return shell('staffing', f"{CFG['conference']} - Booth calendar", body)

# ------------------------------------------------------------------ leaderboard
def render_leaders():
    prizes = ''.join(f'<li><strong>{E(p["place"])}</strong> &mdash; {E(p["prize"])}</li>' for p in CFG['prizes'])
    body = f"""<span class="mvx-eyebrow">{E(CFG['conference'])} &middot; Contest</span>
<h1>Leaderboard</h1>
<div class="sub">{E(CFG['scoring'])}</div>
{NOSYNC}
<div class="sec"><h2>Prizes</h2><ul class="mvx-benefits">{prizes}</ul></div>
<div id="board"></div>
<div id="tiles" class="mvx-statgrid"></div>
<div class="syncpill" id="syncpill">&nbsp;</div>
<script>{wire(src('_parts/leaders.0.js'))}</script>"""
    return shell('leaders', f"{CFG['conference']} - Leaderboard", body)

# ------------------------------------------------------------------ happy hour
def render_happyhour():
    hh = CFG['happy_hour']
    # RSVP list: names from config; an entry with an "id" is on the target
    # list and links to that physician's card.
    rows = []
    for r in hh.get('rsvps', []):
        tag = (f' &mdash; <a href="{SLUG}.html#{E(r["id"])}">on target list</a>'
               if r.get('id') else '')
        rows.append(f'<li><strong>{E(r["name"])}</strong>{tag}</li>')
    rsvps = (f'<div class="sec"><h2>RSVPs ({len(rows)})</h2>'
             f'<ul class="mvx-benefits">{"".join(rows)}</ul></div>'
             if rows else f'<div class="emptystate">{E(hh["empty_state"])}</div>')
    body = f"""<span class="mvx-eyebrow">{E(hh['when'])}</span>
<h1>{E(hh['title'])}</h1>
<div class="sub">{E(hh['where'])}</div>
{rsvps}"""
    return shell('happyhour', f"{CFG['conference']} - {hh['title']}", body)

# ------------------------------------------------------------------ invites
def render_invites():
    cards = []
    for inv in CFG['invites']:
        if inv['url']:
            qr = (f'<img class="qr" alt="QR code" src="https://api.qrserver.com/v1/create-qr-code/'
                  f'?size=320x320&amp;data={html.escape(inv["url"], quote=True)}">')
            link = f'<a href="{E(inv["url"])}" target="_blank">{E(inv["url"])} &#8599;</a>'
        else:
            qr = '<div class="qrempty">QR appears here once the link is set</div>'
            link = '<span style="color:var(--text-muted)">Link not set yet</span>'
        cards.append(f'<div class="icard"><span class="tag">{E(inv["sub"])}</span>'
                     f'<div class="ititle">{E(inv["title"])}</div>{qr}<div class="ilink">{link}</div></div>')
    body = f"""<span class="mvx-eyebrow">{E(CFG['conference'])}</span>
<h1>Invites</h1>
<div class="sub">Scan at the booth or in the demo room, or text the link.</div>
<div class="mvx-notice">Both links are still blank in <code>config.json</code>. Add the URLs and rebuild &mdash; the QR codes generate themselves.</div>
<div class="icards">{''.join(cards)}</div>"""
    return shell('invites', f"{CFG['conference']} - Invites", body)

# ------------------------------------------------------------------ event info
def render_info():
    hall = ''.join(f'<tr><td>{E(d["label"])}</td><td>{E(d["hall_open"])}&ndash;{E(d["hall_close"])} MT</td></tr>'
                   for d in CFG['days'] if d['kind'] == 'show')
    setup = next(d for d in CFG['days'] if d['kind'] == 'setup')
    tdn = next(d['teardown'] for d in CFG['days'] if d.get('teardown'))
    prizes = ''.join(f'<li><strong>{E(p["place"])}</strong> &mdash; {E(p["prize"])}</li>' for p in CFG['prizes'])
    dr = CFG['demo_room']
    body = f"""<span class="mvx-eyebrow">{E(CFG['city'])} &middot; {E(CFG['dates'])}</span>
<h1>Event info</h1>
<div class="sub">Everything in one page.</div>

<div class="sec"><h2>Booth</h2>
<p>Booth <strong>{E(CFG['booth'])}</strong>. {E(dr['name'])}: <strong>{E(dr['number'])}</strong>.</p>
<table class="kv">{hall}</table>
<p class="note">Setup {E(setup['label'])}, {E(setup['window'])} &mdash; {' &middot; '.join(E(x) for x in setup['crew'])} ({E(setup['crew_note'])}). Teardown Wednesday, {E(tdn['window'])} &mdash; {' &middot; '.join(E(x) for x in tdn['crew'])} ({E(tdn['crew_note'])}).</p>
<p class="note">The exhibit hall does not open until Monday. Sunday is setup only.</p></div>

<div class="sec"><h2>Hotel</h2><p>{E(CFG['hotel'])}</p></div>
<div class="sec"><h2>Badges</h2><p>{E(CFG['badge_pickup'])}</p></div>

<div class="sec"><h2>{E(CFG['happy_hour']['title'])}</h2>
<p>{E(CFG['happy_hour']['when'])}<br>{E(CFG['happy_hour']['where'])}</p>
<p class="note">The hall closes at 4:00 PM Monday, so there is an hour in between.</p></div>

<div class="sec"><h2>Lead capture and contest</h2>
<p>{E(CFG['scoring'])}</p>
<ul class="mvx-benefits">{prizes}</ul>
<p class="note">Capture from the physician's card on the target list. Captures work offline and flush when signal returns.</p></div>

<p class="mvx-rxnote">All devices are prescription-only, for use by trained physicians. See each product's Instructions for Use for complete indications, contraindications, warnings, and precautions.</p>"""
    return shell('info', f"{CFG['conference']} - Event info", body)

# ------------------------------------------------------------------ landing
def render_index():
    blurb = {
        'targets':   f'{len(PHYS)} {CFG["specialty"].lower()} ranked by annual core volume, with talk tracks and KOL context. Filter by territory or tier, and capture badge photos from the card.',
        'coverage':  'Who has been reached and which territories still need attention. Flags territories with no rep on site.',
        'leaders':   'Points for every lead captured, updated live. A badge photo is one point; a photo with a note is two.',
        'staffing':  f'Who is at booth {CFG["booth"]} and the demo room, Sunday setup through Wednesday teardown.',
        'happyhour': f'{CFG["happy_hour"]["when"]} at {CFG["happy_hour"]["where"]}.',
        'tips':      'Narwhal setup, operation and watchouts, plus the answers physicians ask for most. Works offline.',
        'invites':   'QR codes and textable links for the happy hour and demo room booking.',
        'info':      'Hotel, badges, exhibit hours, lead capture, prizes and links.',
    }
    tag = {
        'targets':   f'{len(PHYS)} physicians',
        'coverage':  'Live status',
        'leaders':   'Contest',
        'staffing':  f'Booth {CFG["booth"]}',
        'happyhour': 'Mon 5:00 PM',
        'tips':      'Field reference',
        'invites':   'QR codes',
        'info':      'Logistics',
    }
    cards = ''.join(
        f'<a class="tilecard" href="{fn}"><span class="tag">{E(tag[k])}</span>'
        f'<div class="title">{E(label)}</div><div class="desc">{E(blurb[k])}</div></a>'
        for k, label, fn in PAGES if k != 'index')
    body = f"""<span class="mvx-eyebrow">{E(CFG['dates'])} &middot; Booth {E(CFG['booth'])}</span>
<h1>{E(CFG['conference'])}</h1>
<div class="sub">{E(CFG['city'])} &middot; {E(CFG['hotel'])}</div>
<div class="mvx-notice">On a phone, tap <strong>Share &rarr; Add to Home Screen</strong> to install this and keep it working without signal.</div>
<div class="cards">{cards}</div>
<p class="mvx-rxnote">All devices are prescription-only, for use by trained physicians. See each product's Instructions for Use for complete indications, contraindications, warnings, and precautions.</p>"""
    return shell('index', f"Maverix - {CFG['conference']}", body)

# ------------------------------------------------------------------ tips (ported)
TIPS_OVERRIDE = """
/* Brand overlay on the ported AABIP reference page. Its own layout CSS is left
   alone - only type, colour and chrome are brought onto the system. */
body{font-family:var(--font-sans)!important;background:var(--page-bg)!important;color:var(--text-body)!important}
h1,h2,h3,h4{font-family:var(--font-display)!important;color:var(--heading)!important;font-weight:700!important}
a{color:var(--link)}
.sub{color:var(--text-secondary)!important}
"""
def render_tips():
    h = rd('_build/_tips-source.html')
    h = re.sub(r'<div class="nav">.*?</div>', '', h, count=1, flags=re.S)
    h = h.replace('<title>AABIP 2026 - Cryo Tips</title>', f'<title>{E(CFG["conference"])} - Cryo Tips</title>')
    h = h.replace('content="AABIP Targets"', f'content="{E(CFG["app_short_name"])}"')
    h = h.replace('demos at AABIP', f'demos at {E(CFG["conference"].split()[0])}')
    h = h.replace('</head>', '<link rel="stylesheet" href="theme.css">'
                             f'<style>{TIPS_OVERRIDE}</style></head>')
    h = h.replace('<body>', '<body>' + header('tips'), 1)
    return reslug(h)

# ------------------------------------------------------------------ sw + manifest
def render_sw(pages):
    core = pages + ['theme.css', 'pages.css'] + FONTS + [
        'manifest.webmanifest', 'icon-192.png', 'icon-512.png',
        'icon-maskable-512.png', 'apple-touch-icon.png', 'favicon.png']
    # Local photo files (photo-chest-N.jpg) live alongside the pages, one per
    # physician who has a same-origin photo rather than an external CDN URL.
    photos = sorted({p['photo'] for p in PHYS if p.get('photo') and not p['photo'].startswith('http')})
    # Hash the CONTENTS of every precached file, not just their names. Hashing
    # names alone means a changed icon, stylesheet, page or photo ships with
    # the same VERSION, the service worker never invalidates, and reps keep
    # the old copy until they clear site data - which nobody does mid-conference.
    h = hashlib.sha1(CFG['sync_endpoint'].encode())
    for f in core + photos:
        h.update(f.encode())
        fp = os.path.join(HERE, f)
        if os.path.exists(fp):
            with open(fp, 'rb') as fh: h.update(fh.read())
    ver = h.hexdigest()[:12]
    lst = ','.join("'%s'" % f for f in core)
    plst = ','.join("'%s'" % f for f in photos)
    return f"""// Generated by build.py - do not edit by hand.
const VERSION='{ver}';
const SHELL='shell-'+VERSION;
const MEDIA='media-'+VERSION;
const PHOTOS=[{plst}];
const CORE=[{lst}];

self.addEventListener('install',function(e){{
  e.waitUntil(caches.open(SHELL).then(function(c){{return c.addAll(CORE);}})
    // Physician photos are precached one by one so a single missing file can't
    // fail the install; the booth hall has poor signal, so they must work offline.
    .then(function(){{return caches.open(MEDIA);}})
    .then(function(c){{return Promise.all(PHOTOS.map(function(p){{return c.add(p).catch(function(){{}});}}));}})
    .then(function(){{return self.skipWaiting();}}));}});

self.addEventListener('activate',function(e){{
  e.waitUntil(caches.keys().then(function(keys){{
    return Promise.all(keys.map(function(k){{
      if(k!==SHELL&&k!==MEDIA)return caches.delete(k);}}));
  }}).then(function(){{return self.clients.claim();}}));}});

self.addEventListener('fetch',function(e){{
  var req=e.request;
  if(req.method!=='GET')return;                       // never touch sync POSTs
  var url=new URL(req.url);
  if(url.hostname==='script.google.com')return;       // sync endpoint is live-only

  if(req.mode==='navigate'||(url.origin===location.origin&&url.pathname.endsWith('.html'))){{
    // network-first so a redeploy lands, cache fallback so the booth still works offline
    e.respondWith(fetch(req).then(function(res){{
      var copy=res.clone();caches.open(SHELL).then(function(c){{c.put(req,copy);}});return res;
    }}).catch(function(){{return caches.match(req).then(function(m){{
      return m||caches.match('{FILE["targets"]}');}});}}));
    return;}}

  if(url.origin===location.origin&&/\\.(css|js|json|webmanifest)$/i.test(url.pathname)){{
    // Stylesheets and scripts change between builds, often mid-conference.
    // Cache-first left reps on the previous build until a second reload, so
    // these are network-first with a cache fallback: current when online,
    // still works in the hall when not.
    e.respondWith(fetch(req).then(function(res){{
      var copy=res.clone();caches.open(SHELL).then(function(c){{c.put(req,copy);}});return res;
    }}).catch(function(){{return caches.match(req);}}));
    return;}}

  if(url.origin===location.origin){{                    // fonts, icons, local photos
    e.respondWith(caches.match(req).then(function(m){{
      if(m)return m;
      return fetch(req).then(function(res){{
        if(res.ok){{var copy=res.clone();caches.open(MEDIA).then(function(c){{c.put(req,copy);}});}}
        return res;}});}}));
    return;}}

  if(req.destination==='image'||/\\.(jpg|jpeg|png|webp|gif)(\\?|$)/i.test(url.pathname)){{
    // physician photos live on many hospital CDNs - cache-first, opaque is fine
    e.respondWith(caches.match(req).then(function(m){{
      if(m)return m;
      return fetch(req).then(function(res){{
        var copy=res.clone();caches.open(MEDIA).then(function(c){{c.put(req,copy);}});return res;
      }}).catch(function(){{return new Response('',{{status:504}});}});}}));}}
}});
"""

def render_manifest():
    return json.dumps({
        "name": f"{CFG['conference']} Targets - Maverix",
        "short_name": CFG['app_short_name'],
        "description": f"Physician target list and booth schedule for {CFG['conference']}, Booth {CFG['booth']}.",
        "start_url": "index.html", "scope": "./", "display": "standalone",
        "orientation": "portrait-primary", "background_color": "#F2F2F6",
        "theme_color": CFG['theme'],
        "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
                  {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
        "shortcuts": [{"name": "Target list", "url": FILE['targets']},
                      {"name": "Coverage", "url": FILE['coverage']},
                      {"name": "Calendar", "url": FILE['staffing']}],
    }, indent=1)

RENDER = {'index': render_index, 'targets': render_targets, 'coverage': render_coverage,
          'leaders': render_leaders, 'staffing': render_staffing, 'happyhour': render_happyhour,
          'tips': render_tips, 'invites': render_invites, 'info': render_info}

def main():
    written = []
    for key, _, fn in PAGES:
        n = wr(fn, RENDER[key]()); written.append(fn)
        print(f"  {fn:<28}{n:>9,} bytes")
    print(f"  {'sw.js':<28}{wr('sw.js', render_sw(written)):>9,} bytes")
    print(f"  {'manifest.webmanifest':<28}{wr('manifest.webmanifest', render_manifest()):>9,} bytes")
    print(f"\n{len(written)} pages + sw + manifest, slug '{SLUG}', {len(PHYS)} physicians")
    if not CFG['sync_endpoint'].startswith('https://'):
        print("\n  !! sync_endpoint is still a placeholder - checkboxes will not persist")

if __name__ == '__main__':
    main()
