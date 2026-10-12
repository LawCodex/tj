#!/usr/bin/env python3
"""Convert archived mmk.tj legislation pages (_raw/tj/html/*.html.gz, from tj_wayback.py) to Markdown.

Only Drupal nodes of type "legislation" (article.node-legislation) are converted; the other
captured pages (news, articles) are ignored. When several captures/aliases resolve to the same
node, the newest capture wins.
"""
import gzip, os, re, sys, urllib.parse
from bs4 import BeautifulSoup, NavigableString, Tag

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
RAW = os.path.abspath(os.path.join(REPO, '..', '_raw', 'tj'))
RETRIEVED = '2026-10-12'

KINDS = ['part', 'section', 'subsection', 'chapter', 'paragraph', 'article']
PAT = {
    'part': re.compile(r'^(қисми\s+(умумӣ|махсус|[IVXLC\d]+)|(умумӣ|махсус)\s+қисм|часть\s)', re.I),
    'section': re.compile(r'^(фасли\s+([IVXLC\d]+|[а-яӣӯқғҳҷ]+(ум|юм)\b)|раздел\s)', re.I),
    'subsection': re.compile(r'^(зерфасли\s+[IVXLC\d]+|подраздел\s)', re.I),
    'chapter': re.compile(r'^(боби\s+([IVXLC\d]+|[а-яӣӯқғҳҷ]+(ум|юм)\b)|глава\s)', re.I),
    'paragraph': re.compile(r'^(§\s*\d|параграфи\s+\d|параграф\s+\d)', re.I),
    'article': re.compile(r'^(моддаи\s+\d|статья\s+\d)', re.I),
}
DIRS = {'constitution': 'konstitutsiya', 'constitutional_law': 'qonunhoi-konstitutsioni',
        'code': 'kodeksho', 'law': 'qonunho', 'other': 'digar'}


def kind_of(t):
    for k in KINDS:
        if PAT[k].match(t):
            return k
    return None


def clean(t):
    t = t.replace('\xa0', ' ')
    t = re.sub(r'[ \t\r\f\v]+', ' ', t)
    return t.strip()


def md_escape(t):
    t = re.sub(r'^(#+)', r'\\\1', t)
    t = re.sub(r'^(\d+)([.)]) ', r'\1\\\2 ', t)
    t = re.sub(r'^([-+*>]) ', r'\\\1 ', t)
    return t


def inline(node):
    """Text with <em>/<i> kept as Markdown italics (marks superseded wording in Tajik consolidated texts)."""
    out = []
    for c in node.children:
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif c.name == 'br':
            out.append('\n')
        elif c.name in ('em', 'i'):
            t = inline(c)
            if t.strip():
                lead = t[:len(t) - len(t.lstrip())]
                trail = t[len(t.rstrip()):]
                out.append(f'{lead}*{t.strip()}*{trail}')
            else:
                out.append(t)
        elif c.name in ('script', 'style'):
            continue
        else:
            out.append(inline(c))
    return ''.join(out)


def plain(node):
    return clean(node.get_text(' '))


def table_md(tbl):
    rows = []
    for tr in tbl.find_all('tr'):
        cells = [clean(td.get_text(' ')).replace('|', '\\|') for td in tr.find_all(['td', 'th'])]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ''
    n = max(len(r) for r in rows)
    rows = [r + [''] * (n - len(r)) for r in rows]
    return '\n'.join(['| ' + ' | '.join(rows[0]) + ' |', '|' + ' --- |' * n] +
                     ['| ' + ' | '.join(r) + ' |' for r in rows[1:]])


def convert(body):
    blocks = []
    for el in body.find_all(['p', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div'], recursive=True):
        if el.name != 'table' and el.find_parent('table') is not None:
            continue
        if el.name == 'div' and el.find(['p', 'div', 'table', 'li']) is not None:
            continue
        if el.name == 'table':
            m = table_md(el)
            if m:
                blocks.append(['raw', m])
            continue
        if el.name == 'p' and el.find_parent('li') is not None:
            continue
        txt = plain(el)
        if not txt:
            continue
        k = kind_of(txt) if len(txt) < 300 else None
        if k:
            blocks.append(['h', k, txt])
            continue
        strong = clean(' '.join(x.get_text(' ') for x in el.find_all(['strong', 'b'])))
        if strong == txt and blocks and blocks[-1][0] == 'h' and blocks[-1][1] != 'article' and len(txt) < 300:
            blocks[-1][2] += ' ' + txt          # heading title on its own line
            continue
        t = '\n'.join(clean(l) for l in inline(el).split('\n') if clean(l))
        t = re.sub(r'\*\s*\*', '', t)
        for ln in t.split('\n'):
            blocks.append(['p', ln])
    return blocks


def render(blocks):
    present = [k for k in KINDS if any(b[0] == 'h' and b[1] == k for b in blocks)]
    level = {k: min(2 + i, 6) for i, k in enumerate(present)}
    out = []
    for b in blocks:
        if b[0] == 'h':
            out.append('#' * level[b[1]] + ' ' + b[2])
        elif b[0] == 'p':
            out.append(md_escape(b[1]))
        else:
            out.append(b[1])
    return '\n\n'.join(out) + '\n'


TR = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюяғӣқӯҳҷ',
              ['a', 'b', 'v', 'g', 'd', 'e', 'yo', 'zh', 'z', 'i', 'y', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's',
               't', 'u', 'f', 'kh', 'ts', 'ch', 'sh', 'sh', '', 'y', '', 'e', 'yu', 'ya', 'gh', 'i', 'q', 'u', 'h', 'j']))


def slug(s, n=70):
    s = ''.join(TR.get(c, c) for c in s.lower())
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:n].rstrip('-')


MONTHS = {'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'мая': 5, 'июн': 6, 'июл': 7, 'авг': 8,
          'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12}


def field(art, name):
    f = art.select_one(f'.field-name-field-{name} .field-item')
    return clean(f.get_text(' ')) if f else ''


def yq(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def classify(title, cls):
    t = title.upper()
    c = cls.upper()
    if t.startswith('КОНСТИТУТСИЯИ'):
        return 'constitution'
    if 'КОНСТИТУТСИОН' in t[:40] or 'КОНСТИТУТСИОН' in c:
        return 'constitutional_law'
    if t.startswith('КОДЕКС') or 'КОДЕКС' in c:
        return 'code'
    if t.startswith('ҚОНУН') or c.startswith('ҚОНУН'):
        return 'law'
    return 'other'


def main():
    nodes = {}
    for fn in os.listdir(os.path.join(RAW, 'html')):
        if not fn.endswith('.html.gz'):
            continue
        raw = gzip.open(os.path.join(RAW, 'html', fn)).read().decode('utf-8', 'replace')
        head, _, s = raw.partition('\n')
        path, ts, orig = head.split('\t')
        if 'node-legislation' not in s:
            continue
        m = re.search(r'<article id="node-(\d+)"[^>]*node-legislation', s)
        if not m:
            continue
        nid = m.group(1)
        if nid not in nodes or ts > nodes[nid][0]:
            nodes[nid] = (ts, orig, s)
    stats = {}
    for nid, (ts, orig, s) in sorted(nodes.items(), key=lambda x: int(x[0])):
        soup = BeautifulSoup(s, 'lxml')
        art = soup.select_one('article.node-legislation')
        h1 = soup.select_one('h1#page-title') or soup.select_one('h1.title') or soup.find('h1')
        title = clean(h1.get_text(' ')) if h1 else ''
        body = art.select_one('.field-name-body')
        if body is None:
            continue
        blocks = convert(body)
        if not blocks:
            continue
        cls, num, status = field(art, 'classification'), field(art, 'number'), field(art, 'status')
        date = field(art, 'date')
        dm = re.search(r'(\d{2})[./](\d{2})[./](\d{4})', date)
        iso = f'{dm.group(3)}-{dm.group(2)}-{dm.group(1)}' if dm else None
        if not iso:
            dm = re.search(r'(\d{4})-(\d{2})-(\d{2})', date)
            iso = dm.group(0) if dm else None
        if not iso:
            dm = re.search(r'(\d{1,2})\s+([А-Яа-яӢӣӮӯ]+),?\s+(\d{4})', date)
            if dm and dm.group(2).lower()[:3] in MONTHS:
                iso = f'{dm.group(3)}-{MONTHS[dm.group(2).lower()[:3]]:02d}-{int(dm.group(1)):02d}'
        lang = 'tg'
        lab = art.select_one('.form-type-item')
        if lab and 'Русский' in lab.get_text():
            lang = 'ru'
        typ = classify(title, cls)
        st = 'in_force' if 'амал' in status.lower() and 'қувва' not in status.lower() else (
            'repealed' if status and ('қувваи' in status.lower() or 'бекор' in status.lower()) else 'unknown')
        name = slug(title) or ('node-' + nid)
        name = f'{name}-{nid}'
        sub = DIRS[typ]
        rel = os.path.join(lang, sub, (iso[:4] if (typ == 'law' and iso) else ''), name + '.md')
        rel = os.path.normpath(rel)
        canon = orig.replace('http://', 'https://')
        fm = ['---', f'title: {yq(title)}', f'identifier: "mmk.tj/node/{nid}"']
        if num:
            fm.append(f'number: {yq(num)}')
        fm += [f'type: {typ if typ != "law" else "act"}', 'jurisdiction: tj', f'language: {lang}']
        if iso:
            fm.append(f'date: {iso}')
        if cls:
            fm.append(f'classification: {yq(cls)}')
        fm += [f'last_amended: {ts[:4]}-{ts[4:6]}-{ts[6:8]}  # consolidated text as captured on this date',
               f'status: {st}']
        if status:
            fm.append(f'mmk_status: {yq(status)}')
        fm += [f'source: "{canon}"', f'archived_source: "https://web.archive.org/web/{ts}/{orig}"',
               f'retrieved: {RETRIEVED}', '---', '']
        md = '\n'.join(fm) + f'\n# {title}\n\n' + render(blocks)
        out = os.path.join(REPO, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(md)
        stats[(lang, typ, st)] = stats.get((lang, typ, st), 0) + 1
    for k, v in sorted(stats.items()):
        print(k, v)


if __name__ == '__main__':
    main()
