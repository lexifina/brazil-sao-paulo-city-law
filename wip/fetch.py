"""Private (not published). Fetches the Lei Orgânica and the Leis of the Município de São Paulo from the Prefeitura's
Portal da Legislação Municipal (legislacao.prefeitura.sp.gov.br, Casa Civil / CADLEM).

    python -X utf8 fetch.py --lom
    python -X utf8 fetch.py --years 2026-1892      # listing + every law page (+ its Detalhes page when unaltered)

One process, one request at a time, >= 3 s apart (shared helper ../world-law/br_city_get.py); cache .cache/raw.
Index: .cache/index.json {slug: {title, ementa, situacao, year}}; .cache/years-done.json lists the years whose law
pages are all fetched.
"""
import argparse, json, re, sys, html
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'world-law'))
from br_city_get import Host  # noqa: E402

BASE = 'https://legislacao.prefeitura.sp.gov.br'
CACHE = HERE / '.cache'
H = Host(CACHE, 'legislacao.prefeitura.sp.gov.br', delay=3.0)
LOM = '/leis/lei-0-de-04-de-abril-de-1990'


def detail_url(page, slug):
    m = re.search(r'href="(/[^"]*/detalhe/[0-9a-f]+)"', page)
    return BASE + m.group(1) if m else None


def law(slug, need_detail=True):
    b = H.get(BASE + '/leis/' + slug)
    if b is None:
        return None
    if need_detail:
        d = detail_url(b.decode('utf-8', 'replace'), slug)
        if d:
            H.get(d)
    return b


def listing(year):
    out, page = [], 1
    data = f'limite=100&tipo%5B%5D=LEI&ano-inicial={year}&ano-final={year}'
    while True:
        url = f'{BASE}/busca?ano-inicial={year}' if page == 1 else f'{BASE}/busca/pg/{page}?ano-inicial={year}'
        s = H.get(url, data=data).decode('utf-8', 'replace')
        for blk in re.findall(r'(?s)<div class="bx-resultado">(.*?)</ul>\s*</div>', s):
            m = re.search(r'<a href="/leis/([^"]+)">\s*<h4>([^<]*)</h4>\s*<p>(.*?)</p>', blk, re.S)
            if not m:
                continue
            sit = [html.unescape(x).strip() for x in re.findall(r'<p>([^<]*)</p>', blk[blk.find('Situa'):])]
            out.append({'slug': m.group(1), 'title': html.unescape(m.group(2)).strip(),
                        'ementa': html.unescape(re.sub(r'<[^>]+>', '', m.group(3))).strip(), 'situacao': sit,
                        'year': year})
        tot = re.search(r'Página (\d+) de (\d+)', s)
        if not tot or int(tot.group(1)) >= int(tot.group(2)):
            return out
        page += 1


def altered(e):
    return any(x for x in e['situacao'] if x != 'SEM REVOGAÇÃO EXPRESSA' and x != 'Não informado')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lom', action='store_true')
    ap.add_argument('--years', default='')
    a = ap.parse_args()
    if a.lom:
        law(LOM[6:])
    idx_p, done_p = CACHE / 'index.json', CACHE / 'years-done.json'
    idx = json.loads(idx_p.read_text(encoding='utf-8')) if idx_p.exists() else {}
    done = json.loads(done_p.read_text(encoding='utf-8')) if done_p.exists() else []
    if a.years:
        y0, y1 = (int(x) for x in a.years.split('-'))
        for y in range(y0, y1 - 1, -1) if y0 >= y1 else range(y0, y1 + 1):
            if y in done:
                continue
            items = listing(y)
            for e in items:
                idx[e['slug']] = e
            idx_p.write_text(json.dumps(idx, ensure_ascii=False, indent=0), encoding='utf-8')
            print(y, len(items), 'listed', flush=True)
            for e in items:
                if any(x == 'REVOGADO(A)' for x in e['situacao']):
                    continue  # wholly revoked: not in force, not fetched
                law(e["slug"], need_detail=not altered(e))
            done.append(y)
            done_p.write_text(json.dumps(done), encoding='utf-8')
            print(y, 'done', flush=True)


if __name__ == '__main__':
    main()
