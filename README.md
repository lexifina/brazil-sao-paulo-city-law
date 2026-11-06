# São Paulo (city): law history in git

Part of [lexifina/global-law](https://github.com/lexifina/global-law), one git history for every country's law: this is the law of Sao Paulo, São Paulo, Brazil, which global-law reads at `brazil/sao-paulo/sao-paulo/acts/`.

The municipal law of the Município de São Paulo, the city of São Paulo (Brazil) as a git history: one file per Artigo, one paragraph per line, so `git blame`, `git log` and `git diff` work line by line. The text is Portuguese, the only official language.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law).

## What this repository holds

| Folder | Act | Versions |
| --- | --- | ---: |
| `lei-organica/` | Lei Orgânica do Município de São Paulo (1990) | 1 |
| `lei-<year>-<number>/` | the municipal Leis the portal does not list as wholly revoked | 1 each |

**Partial, and growing:** the Leis are added year by year, newest first, as the portal's pages are read; the history may still gain earlier commits. An act the portal shows no alteration for is given **as enacted**, credited to the act itself. An altered act (the Lei Orgânica included) is given **only as its text in force**, credited to the portal as the oldest version available: the wordings in between are not reconstructed, so no earlier version is shown rather than a wrong one. State law is in [brazil-sao-paulo-law](https://github.com/lexifina/brazil-sao-paulo-law); federal law in [brazil-law](https://github.com/lexifina/brazil-law).

## Source

[Portal da Legislação Municipal](https://legislacao.prefeitura.sp.gov.br), published by the Prefeitura do Município de São Paulo (Casa Civil, Centro de Referência da Legislação Municipal - CADLEM). Each version names the page it was taken from and that page's sha256, in `data/versions.json`.

## Dates

An unaltered act is dated by its publication in the Diário Oficial da Cidade, as the portal's "Detalhes da Norma" gives it (São Paulo municipal laws almost always take effect on publication). An altered act's text in force is dated by the latest date among the altering acts it links to (its alteration notes and its "Alterações" list); each date is the one in the altering act's portal address, the day it was signed. Commits are at noon in São Paulo.

## How it is built

Lexifina reads the sources listed here and records each act's dated versions, and the laws that made each change, in one corpus file. `tools/build.py` writes this repository from that file, and the same corpus always gives the same commit hashes; `REPRODUCE.md` gives the details and the checks. A model (Claude) wrote Lexifina's code; it wrote no legal text, and no model runs when the history is built.

Each page becomes one file per Art.; headings of the Títulos, Capítulos and Seções stand above the first article under them; `000-titulo.md` holds the title, the ementa and the preamble (for the Lei Orgânica also its table of contents); the Lei Orgânica's Disposições Gerais e Transitórias, numbered from 1 again, are `adt-*`. For the text in force, the earlier wordings the page strikes through and the alteration notes in parentheses ("(Redação dada pela ...)", "(Incluído pela ...)", "(Revogado pela ...)") are left out, as is the portal's notice that the text does not replace the Diário Oficial. Tables are one line per row, with cells separated by ` | `.

## How it is checked

Every version is read back from git on the day it took effect (`tools/check_repo.py`) and must match the corpus; an independent letters-and-digits comparison of every version against the source page must show no difference. Results are in `REPRODUCE.md`.

## What "author" means

The author of each commit is the law that made the text, or, for a consolidated text, the publisher, with an e-mail address that cannot exist; the committer is always Lexifina.

## Limits

Not a complete history: an altered act starts at its text in force. Laws the portal lists as wholly revoked are left out, as are altered laws that link to no dated altering act and pages with no text; `data/` lists what is in. The text is not the official version: only the Diário Oficial da Cidade de São Paulo is authoritative. Text after the last article (place, date, signatures, annexes) stays in the last article's file.

## Licence

See [LICENSE](LICENSE): Brazilian law texts are not protected by copyright (Lei 9.610/1998, art. 8, IV). Fonte: Portal da Legislação Municipal, Prefeitura do Município de São Paulo (Casa Civil, Centro de Referência da Legislação Municipal - CADLEM).
