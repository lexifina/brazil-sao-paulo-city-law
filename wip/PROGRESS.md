# brazil-sao-paulo-city-law (gitlaw-scraper-dell, 2026-10-31)

Private. Municipal tier (Alan's coverage wave via global-law-main-composer). Source: Prefeitura de São Paulo, Portal da
Legislação Municipal (legislacao.prefeitura.sp.gov.br, Casa Civil / CADLEM).
Gates 2026-10-31 18:01-18:04Z: robots.txt = no file (the app's HTML page answers /robots.txt), so no rule; policy: page
"Sobre" says the portal is, under Lei 17.901/2023, an official open-data repository for download; no challenge.
Repo created 18:04Z (br_scaffold.py, one API call), scaffold 0d54d19.

- fetch.py: --lom; --years 2026-1892 (POST /busca filter tipo LEI per year, 100 a page; each law page not listed as
  wholly revoked, plus its Detalhes page when the listing shows no alteration). One process, >= 3 s apart
  (../world-law/br_city_get.py). PIDs in my-pids.txt.
- parse.py --today YYYY-MM-DD: 10-lei-organica, then 30-lei-<year>-NN (50 a part) for each year in .cache/years-done.json.
  Parts with .PUBLISH are never rewritten.
- Verify: check_letters.py <part> (0 mismatches), build into .tmp-build + check.py clean + audit_push [], then PUBLISH.
- Rule: unaltered = as enacted, dated by Data de publicação (Detalhes); altered = text in force, credited to the portal,
  dated by the latest date in the altering acts' addresses (notes + Alterações list).
- 18:08Z: 10-lei-organica PUBLISHed; main 23a9834 (autopush).
- 2026-10-31T18:28:40Z: 30-lei-2026-01..04 (187 Leis of 2026; 1 left out: altered, no dated alteration) PUBLISHed.
