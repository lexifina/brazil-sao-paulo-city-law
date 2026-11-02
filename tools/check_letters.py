"""Independent letters-and-digits check of every version against its source page (regular expressions only, no HTML
parser, none of the builder's code).

    python -X utf8 check_letters.py [part.json ...]

For each version: the page's text block (from the div after the ementa heading to the portal's notice "Este texto não
substitui ..."), with struck-through runs (<del>, <s>, <strike>) and the alteration notes in parentheses removed, reduced
to letters and digits, must equal the version's unit files reduced the same way, each unit found at its place in
document order (for the Lei Orgânica the title unit carries the table of contents, which comes first on the page).
"""
import hashlib, html, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = re.compile(r'\(\s*(?:Nova\s+reda|Reda[çc][ãa]o\s+dada|Acresc|Revogad|Inclu[íi]d|Alterad|Renumerad|Suprimid|Vide\b|'
                  r'Vig[êe]n|Regulamentad|Modificad|Declarad|Suspens|Derrogad|Prorrogad|Acrescentad)[^()]*'
                  r'(?:\([^()]*\)[^()]*)*\)', re.I)


def ld(s):
    return ''.join(ch for ch in s if ch.isalnum())


def page_text(raw):
    s = raw.decode('utf-8', 'replace')
    i = s.index('<div class="col s12 customStyle">')
    j = s.find('<div class="bx-mensagem', i)
    s = s[i:j if j > 0 else len(s)]
    s = re.sub(r'(?is)<script.*?</script>|<!--.*?-->', '', s)
    while True:
        t = re.sub(r'(?is)<(del|s|strike)\b[^>]*>(?:(?!<(?:del|s|strike)\b).)*?</\1\s*>', '', s)
        if t == s:
            break
        s = t
    s = re.sub(r'(?is)<[^>]*line-through[^>]*>.*?</span>', '', s)
    s = html.unescape(re.sub(r'<[^>]+>', ' ', s))
    s = re.sub(r'\s+', ' ', s)
    return NOTE.sub(' ', s)


def main(paths):
    bad = total = 0
    for p in paths:
        c = json.load(open(p, encoding='utf-8'))
        for a in c['acts']:
            for v in a['versions']:
                raw = (HERE / '.cache' / 'raw' / hashlib.sha256(v['source_url'].encode()).hexdigest()).read_bytes()
                assert hashlib.sha256(raw).hexdigest() == v['sha256'], (a['slug'], 'sha256')
                src = ld(page_text(raw))
                rest = {k: ld(re.sub(r'(?m)^#+ ', '', u['text'])) for k, u in v['units'].items()}
                pos = 0
                while rest:
                    hit = None
                    for k, t in rest.items():
                        if t and src.startswith(t, pos) and (hit is None or len(t) > len(rest[hit])):
                            hit = k
                    if hit is None:
                        break
                    pos += len(rest.pop(hit))
                total += 1
                if rest or pos != len(src):
                    bad += 1
                    print(f'MISMATCH {a["slug"]} {v["from"]}: matched {pos}/{len(src)}; next source: '
                          f'{src[pos:pos + 80]!r}; unplaced: {list(rest)[:5]}')
    print(f'{total} versions checked, {bad} mismatches')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1:] or sorted(str(p) for p in (HERE / 'corpus.d').glob('*.json'))) else 0)
