#!/usr/bin/env python3
"""Tajikistan: harvest legislation pages of the National Legislation Centre under the President
(Маркази миллии қонунгузорӣ, https://mmk.tj) from the Internet Archive, because mmk.tj itself
does not answer from outside Tajikistan (connection time-outs) and the Ministry of Justice
database (mmih.adlia.tj) only shows a truncated preview without a (paid/registered) login.

Step 1 (cdx):   list captures of mmk.tj/content/* and mmk.tj/node/* -> _raw/tj/snapshots.tsv
Step 2 (fetch): download the newest good capture of each candidate page -> _raw/tj/html/
Usage: tj_wayback.py cdx | fetch
"""
import gzip, hashlib, os, re, sys, time, urllib.parse, zlib, requests

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '_raw', 'tj')
UA = 'LawCodex/1.0 (+https://github.com/LawCodex)'
DELAY = 4.0
LEGAL_PREFIXES = ('қонуни', 'кодекси', 'конститутсияи', 'конститутсия')


def get(s, url, params=None, timeout=300):
    for a in range(6):
        try:
            r = s.get(url, params=params, timeout=timeout, stream=True)
            if r.status_code == 200:
                body = r.raw.read(decode_content=False)
                for _ in range(3):
                    if body[:2] == b'\x1f\x8b':
                        try:
                            body = zlib.decompress(body, 47); continue
                        except Exception:
                            pass
                    break
                return body
            if r.status_code in (404, 403) or r.status_code >= 500:
                return None
            print('HTTP', r.status_code, url, file=sys.stderr, flush=True)
        except Exception as e:
            print('ERR', url, str(e)[:120], file=sys.stderr, flush=True)
            time.sleep(60 if 'Tunnel' in str(e) else 10)
            continue
        time.sleep(15 * (a + 1))
    return None


def cdx(s):
    best = {}
    for prefix in ('mmk.tj/content/', 'mmk.tj/node/'):
        cache = os.path.join(RAW, 'cdx_' + prefix.split('/')[1] + '.txt')
        if not os.path.exists(cache):
            body = get(s, 'https://web.archive.org/cdx/search/cdx', params=dict(
                url=prefix, matchType='prefix', filter='statuscode:200', fl='urlkey,timestamp,original,length'), timeout=900)
            if body is None:
                raise SystemExit('cdx failed')
            open(cache, 'wb').write(body)
        for line in open(cache, encoding='utf-8', errors='replace'):
            p = line.split()
            if len(p) != 4:
                continue
            key, ts, orig, ln = p
            m = re.match(r'^tj,mmk\)/(content/[^?/]+|node/\d+)$', key)
            if not m:
                continue
            path = m.group(1)
            if path.startswith('content/'):
                slug = urllib.parse.unquote(path[8:])
                if not slug.startswith(LEGAL_PREFIXES):
                    continue
            best.setdefault(path, []).append((ts, orig))
    with open(os.path.join(RAW, 'snapshots.tsv'), 'w') as f:
        for path, caps in sorted(best.items()):
            caps = sorted(set(caps), reverse=True)[:3]
            f.write(path + '\t' + ' '.join(f'{t}|{o}' for t, o in caps) + '\n')
    print(len(best), 'candidate pages')


def fetch(s):
    os.makedirs(os.path.join(RAW, 'html'), exist_ok=True)
    rows = [l.rstrip('\n').split('\t') for l in open(os.path.join(RAW, 'snapshots.tsv'))]
    # content aliases (titles known to be acts) first, then numeric nodes
    rows.sort(key=lambda r: (not r[0].startswith('content/'), r[0]))
    import threading
    from concurrent.futures import ThreadPoolExecutor
    local = threading.local()

    def job(row):
        if not hasattr(local, 's'):
            local.s = requests.Session(); local.s.headers['User-Agent'] = UA
        one(local.s, *row)

    with ThreadPoolExecutor(3) as ex:
        list(ex.map(job, rows))
    print('done')


def one(s, path, caps):
        fn = os.path.join(RAW, 'html', hashlib.md5(path.encode()).hexdigest() + '.html.gz')
        if os.path.exists(fn) or os.path.exists(fn + '.none'):
            return
        ok = False
        for cap in caps.split():
            ts, orig = cap.split('|', 1)
            body = get(s, f'https://web.archive.org/web/{ts}id_/{orig}')
            time.sleep(DELAY)
            if body and b'<html' in body[:5000].lower():
                with gzip.open(fn, 'wb') as f:
                    f.write(f'{path}\t{ts}\t{orig}\n'.encode() + body)
                ok = True
                break
        if not ok:
            open(fn + '.none', 'w').close()


if __name__ == '__main__':
    s = requests.Session(); s.headers['User-Agent'] = UA
    {'cdx': cdx, 'fetch': fetch}[sys.argv[1]](s)
