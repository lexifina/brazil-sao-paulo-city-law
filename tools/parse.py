"""Builds corpus.d parts for the Município de São Paulo from the retrieved Portal da Legislação Municipal pages
(no network).

    python -X utf8 parse.py --today YYYY-MM-DD [--part-size 50]

Each law page of the portal shows the act's text with its later alterations worked in: earlier wordings struck through
(<del>), each alteration noted in parentheses with a link to the altering act ("(Redação dada pela Emenda nº 6/1991)",
"(Incluído pela ...)", "(Revogado pela ...)"), and an "Alterações" list of the altering acts. An act with no such note,
nothing struck through and no alteration in its list is given as enacted, credited to the act itself and dated by its
publication in the Diário Oficial da Cidade (the portal's "Detalhes da Norma"). An altered act is given only as its
text in force, credited to the portal as the oldest version available, dated by the latest date of the altering acts
it links to.
"""
import argparse, html, json, re, sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import br_lib  # noqa: E402
from br_lib import lines_of, units_of, write_part, sha, norm  # noqa: E402

# The Lei Orgânica's closing part is "Disposições Gerais e Transitórias", whose articles start again at 1 (adt-*).
br_lib.ADT = re.compile(r'DISPOSI[ÇC][ÕO]ES\s+(?:GERAIS\s+E\s+|CONSTITUCIONAIS\s+)?TRANSIT[ÓO]RIAS', re.I)

CACHE = HERE / '.cache'
BASE = 'https://legislacao.prefeitura.sp.gov.br'
BLOCK = {'p', 'div', 'br', 'tr', 'li', 'table', 'tbody', 'thead', 'ul', 'ol', 'center', 'blockquote', 'h1', 'h2', 'h3',
         'h4', 'h5', 'h6'}
VOID = {'br', 'img', 'meta', 'link', 'hr', 'input', 'col', 'area', 'base', 'wbr'}
NOTE = re.compile(r'\(\s*(?:Nova\s+reda|Reda[çc][ãa]o\s+dada|Acresc|Revogad|Inclu[íi]d|Alterad|Renumerad|Suprimid|'
                  r'Vide\b|Vig[êe]n|Regulamentad|Modificad|Declarad|Suspens|Derrogad|Prorrogad|Acrescentad)'
                  r'(?:[^()]|\([^()]*\))*\)', re.I)
BOILER = re.compile(r'^Este texto n[ãa]o substitui o original publicado no Di[áa]rio Oficial', re.I)
MONTHS = {m: i + 1 for i, m in enumerate(['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho', 'agosto',
                                           'setembro', 'outubro', 'novembro', 'dezembro'])}
SLUGDATE = re.compile(r'-de-(\d{1,2})-de-(' + '|'.join(MONTHS) + r')-de-(\d{4})/?$')


class Split(HTMLParser):
    """The text block split into what it shows without struck-through runs (<del>, <s>, <strike>, line-through), the
    struck runs, and the hrefs of links inside alteration notes."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.kept, self.old = [], [], []

    def handle_starttag(self, tag, attrs):
        if re.fullmatch(r'h[1-6]', tag):
            self.kept.append(f'<{tag}>')
        elif tag in BLOCK:
            self.kept.append('<br>')
        a = dict(attrs)
        if tag == 'a' and a.get('href') and not any(e[1] for e in self.stack):
            self.kept.append(f'<a href="{html.escape(a["href"])}">')
        if tag not in VOID:
            st = (a.get('style') or '').lower()
            self.stack.append((tag, tag in ('s', 'strike', 'del') or 'line-through' in st))

    def handle_endtag(self, tag):
        if re.fullmatch(r'h[1-6]', tag):
            self.kept.append(f'</{tag}>')
        elif tag in BLOCK:
            self.kept.append('<br>')
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, d):
        if any(e[1] for e in self.stack):
            self.old.append(d)
        else:
            self.kept.append(html.escape(d, quote=False))


def slug_date(href):
    m = SLUGDATE.search(href.split('?')[0].rstrip('/'))
    if not m:
        return None
    d, mo, y = int(m.group(1)), MONTHS[m.group(2)], int(m.group(3))
    return f'{y:04d}-{mo:02d}-{d:02d}' if 1 <= d <= 31 else None


def text_block(page):
    """The law text: from the div after the ementa heading to the portal's notice."""
    i = page.find('<div class="col s12 customStyle">')
    if i < 0:
        return None
    j = page.find('<div class="bx-mensagem', i)
    if j < 0:
        j = page.find('<div class="bx-leis historyBox"', i)
    return page[page.index('>', i) + 1:j if j > 0 else len(page)]


def history_hrefs(page):
    i = page.find('<div id="historico">')
    if i < 0:
        return []
    j = page.find('</ol>', i)
    return re.findall(r'href="([^"]+)"', page[i:j if j > 0 else i + 200000])


def split(block):
    p = Split()
    p.feed(block)
    p.close()
    kept = ''.join(p.kept)
    lines, notes = [], []
    # note hrefs: links inside an alteration note's parentheses
    note_hrefs = []
    for m in NOTE.finditer(re.sub(r'<br>', ' ', kept)):
        note_hrefs += re.findall(r'href="([^"]+)"', m.group(0))
    kept = re.sub(r'<a href="[^"]*">', '', kept)
    for kind, l in lines_of(kept):
        notes += NOTE.findall(l)
        l = norm(NOTE.sub(' ', l))
        if not l or not re.search(r'\w', l) or BOILER.match(l):
            continue
        lines.append((kind, l))
    return lines, notes, note_hrefs, norm(''.join(p.old))


def is_alteration(n):
    return not re.match(r'^\(\s*(Vide|Regulamentad|Vig[êe]n)', n, re.I)


COUNTRY = {
    'code': 'BR-SP-SAO-PAULO', 'name': 'São Paulo (city)', 'slug': 'brazil-sao-paulo-city', 'lang': 'pt',
    'tz': 'America/Sao_Paulo', 'future_branch': 'futuro',
    'publisher': {'name': 'Prefeitura do Município de São Paulo, Portal da Legislação Municipal (CADLEM)',
                  'email': 'legislacao@prefeitura.sp.gov.br.invalid'},
    'default_in_force_rule': {
        'text': 'Decreto-Lei 4.657/1942 (LINDB) art. 1: unless it says otherwise, a law takes effect 45 days after its '
                'official publication. São Paulo municipal laws almost always say "Esta lei entrará em vigor na data '
                'de sua publicação"; this record dates each act as enacted by its publication in the Diário Oficial '
                'da Cidade (the Lei Orgânica by its latest amendment).',
        'source': 'https://www.planalto.gov.br/ccivil_03/decreto-lei/del4657compilado.htm'},
    'licence_note': 'Texts: Prefeitura do Município de São Paulo, Portal da Legislação Municipal, '
                    'legislacao.prefeitura.sp.gov.br (an official open-data repository under Lei municipal '
                    '17.901/2023). Lei 9.610/1998 art. 8 IV: the texts of laws and other official acts are not '
                    'protected by copyright. Non-official text ("Este texto não substitui o original publicado no '
                    'Diário Oficial da Cidade de São Paulo").',
}
DECISIONS = [
    'An act the portal shows no alteration for (no alteration note, nothing struck through, no altering act listed, '
    'situação "sem revogação expressa" or "não informado") is given as enacted, credited to the act itself and dated '
    'by its publication in the Diário Oficial da Cidade as the portal\'s "Detalhes da Norma" gives it. An altered act '
    'is given only as its text in force, credited to the portal as the oldest version available and dated by the '
    'latest date of the altering acts it links to (in its alteration notes and its "Alterações" list; the date is the '
    'one in each act\'s portal address, the day it was signed). The wordings in between are not reconstructed, so no '
    'earlier version is given rather than a wrong one. An altered act that links to no dated altering act is left '
    'out, as are acts the portal lists as wholly revoked ("REVOGADO(A)").',
    'The text in force leaves out what the page strikes through (earlier wordings) and the alteration notes in '
    'parentheses ("(Redação dada pela ...)", "(Incluído pela ...)", "(Revogado pela ...)", "(Vide ...)"), and the '
    'portal\'s notice "Este texto não substitui o original publicado no Diário Oficial da Cidade de São Paulo".',
    'One file per Art.; headings of the Títulos, Capítulos and Seções stand above the first article under them; '
    '"000-titulo" holds the title, the ementa, the preamble and, for the Lei Orgânica, its table of contents. Text '
    'after the last article (place, date, signatures) stays with the last article. Tables are one line per row, cells '
    'separated by " | "; images are left out.',
]
AI = ["Claude Code (claude-opus-5-5) wrote Lexifina's code and chose the sources. No model output is used as legal "
      "text or dates: every word comes from the Prefeitura's portal pages."]


def raw(url):
    p = CACHE / 'raw' / sha(url.encode())
    return p.read_bytes() if p.exists() else None


def detail(page):
    m = re.search(r'href="(/[^"]*/detalhe/[0-9a-f]+)"', page)
    b = raw(BASE + m.group(1)) if m else None
    if b is None:
        return {}
    t = html.unescape(re.sub(r'<[^>]+>', '\n', re.sub(r'(?is)<script.*?</script>|<style.*?</style>', '', b.decode(
        'utf-8', 'replace'))))
    t = re.sub(r'\s*\n\s*', '\n', t)
    out = {}
    for k, key in (('Data de assinatura', 'signed'), ('Data de publicação', 'published')):
        m = re.search(re.escape(k) + r'\n(\d{2})/(\d{2})/(\d{4})', t)
        if m:
            out[key] = f'{m.group(3)}-{m.group(2)}-{m.group(1)}'
    return out


def act_of(slug, entry, today, lom=False):
    url = BASE + '/leis/' + slug
    b = raw(url)
    if b is None:
        return None, {}, 'not fetched'
    page = b.decode('utf-8', 'replace')
    block = text_block(page)
    if block is None:
        return None, {}, 'no text block'
    lines, notes, note_hrefs, old = split(block)
    hist = history_hrefs(page)
    alter = sorted(d for d in (slug_date(h) for h in note_hrefs + hist) if d)
    sit = entry.get('situacao') or []
    altered = bool(old) or any(is_alteration(x) for x in notes) or bool(hist) or any(
        x not in ('SEM REVOGAÇÃO EXPRESSA', 'Não informado') for x in sit)
    det = detail(page)
    m = re.match(r'lei-(\d+)-de-(\d{1,2})-de-([a-z]+)-de-(\d{4})$', slug)
    if not m or m.group(3) not in MONTHS:
        return None, {}, 'odd slug'
    n, y = int(m.group(1)), m.group(4)
    enacted = det.get('signed') or f'{y}-{MONTHS[m.group(3)]:02d}-{int(m.group(2)):02d}'
    published = det.get('published')
    if lom:
        key, aslug, short = 'lei-organica-1990', 'lei-organica', 'LOM-SP'
        label = 'Lei Orgânica do Município de São Paulo, de 4 de abril de 1990'
    else:
        key = aslug = f'lei-{y}-{n:05d}'
        short, label = f'Lei {n}/{y}', f'Lei nº {n:,}'.replace(',', '.') + f', de {enacted[8:10]}/{enacted[5:7]}/{y}'
    alter = [d for d in alter if d > enacted]
    if altered and not alter:
        return None, {}, 'altered, no dated alteration'
    if not altered and not published:
        return None, {}, 'unaltered, no publication date'
    if lom:  # the table of contents before the text's own heading goes with the title
        cut = next((i for i, (k, l) in enumerate(lines) if i > 0 and k == 'h1'), 0)
        head, lines = lines[:cut], lines[cut:]
    else:
        head = []
    units = units_of(lines, adt=lom)
    if not units or list(units) == ['000-titulo']:
        return None, {}, 'no text'
    if head:
        t = units.get('000-titulo', {'label': 'Título', 'kind': 'title', 'text': ''})
        t['text'] = '\n'.join(['# ' + head[0][1]] + [l for _, l in head[1:]]) + '\n' + t['text'].replace('# ', '', 1)
        units = {'000-titulo': t, **{k: v for k, v in units.items() if k != '000-titulo'}}
    ementa = entry.get('ementa') or ''
    laws = {key: {'label': label, 'title': ementa or label, 'kind': 'law', 'enacted': enacted, 'published': published,
                  'url': url, 'temporary_until': None, 'restores': None, 'note': None}}
    v = {'from': alter[-1] if alter else published, 'source_url': url, 'sha256': sha(b), 'units': units}
    if alter:
        v['note'] = (f'Text in force as kept by the Portal da Legislação Municipal; {label} was altered by acts of '
                     f'{len(set(alter))} date(s), the latest {alter[-1]}.')
    act = {'slug': aslug, 'short': short,
           'title': label + (f' ({ementa})' if ementa and len(ementa) < 160 and not lom else ''),
           'url': url, 'first_law': None if alter else key, 'earlier_laws': [key] if alter else [],
           'versions': [v]}
    return act, laws, 'ok'


def part(name, acts, laws, today, what):
    c = {'country': COUNTRY,
         'sources': [{'name': 'Prefeitura do Município de São Paulo, Portal da Legislação Municipal: ' + what,
                      'url': BASE, 'retrieved': today, 'licence': COUNTRY['licence_note'],
                      'notes': f'{len(acts)} acts in this part.'}],
         'laws': laws, 'acts': acts, 'applies': [], 'decisions': DECISIONS, 'ai_use': AI}
    return write_part(HERE / 'corpus.d', name, c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--today', required=True)
    ap.add_argument('--part-size', type=int, default=50)
    ap.add_argument('--only-year', type=int, help='parse only this year (the others stay as they are)')
    a = ap.parse_args()
    why = {}
    act, l, w = act_of('lei-0-de-04-de-abril-de-1990', {'ementa': 'Lei Orgânica do Município de São Paulo'}, a.today,
                       lom=True)
    print('LOM', w)
    if act and not (HERE / 'corpus.d' / '10-lei-organica.PUBLISH').exists():
        print(part('10-lei-organica', [act], l, a.today, 'the Lei Orgânica do Município'))
    idx_p, done_p = CACHE / 'index.json', CACHE / 'years-done.json'
    idx = json.loads(idx_p.read_text(encoding='utf-8')) if idx_p.exists() else {}
    done = json.loads(done_p.read_text(encoding='utf-8')) if done_p.exists() else []
    left = {}
    for y in sorted(done):
        if a.only_year and int(y) != a.only_year:
            continue
        acts = {}
        for slug, e in sorted(idx.items()):
            if e['year'] != y or slug == 'lei-0-de-04-de-abril-de-1990' or 'REVOGADO(A)' in e['situacao']:
                continue
            act, l, w = act_of(slug, e, a.today)
            why[w] = why.get(w, 0) + 1
            if w != 'ok':
                left[slug] = w
                continue
            if act['slug'] in acts:
                why['duplicate'] = why.get('duplicate', 0) + 1
                continue
            acts[act['slug']] = (act, l)
        order = sorted(acts.values(), key=lambda x: x[0]['slug'])
        for i in range(0, len(order), a.part_size):
            name = f'30-lei-{y}-{i // a.part_size + 1:02d}'
            if (HERE / 'corpus.d' / f'{name}.PUBLISH').exists():
                continue
            chunk = order[i:i + a.part_size]
            laws = {}
            for _, l in chunk:
                laws.update(l)
            print(part(name, [x[0] for x in chunk], laws, a.today, f'the Leis of {y}'), len(chunk))
    lp = HERE / 'left-out.json'
    if a.only_year and lp.exists():
        left = {**{k: v for k, v in json.loads(lp.read_text(encoding='utf-8')).items() if k not in left}, **left}
    lp.write_text(json.dumps(left, indent=0, ensure_ascii=False), encoding='utf-8')
    print(why)


if __name__ == '__main__':
    main()
