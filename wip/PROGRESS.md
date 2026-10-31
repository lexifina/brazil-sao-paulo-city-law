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
- 2026-10-31T18:57:01Z: 30-lei-2025-01..04 (153 Leis of 2025) PUBLISHed (build 341 acts clean).
- 2026-10-31 18:57:49Z: connect timeout (curl 28, 21 s) on a 2024 law page after ~1,000 clean requests; br_city_get wrote .cache/STOP and fetch.py (PID 25152) exited. Treated as a fail per the brief: no retry. Published: LOM + Leis of 2026 and 2025. Year 2024 is partly fetched (not parsed: parse.py only takes years in years-done.json). To resume after a manual check of the host: delete .cache/STOP, run fetch.py --years 2024-1892 (one process, BelowNormal).
- 19:03Z resumed (PID 41236) after confirming the 18:57Z timeout was a local network drop (Porto Velho's SAPL failed in the same 9 s); see SCRAPING-LOG.md.
- 2026-10-31T19:06:15Z: 30-lei-2024-01..04 (153 Leis of 2024) PUBLISHed (build 494 acts clean).
- 2026-10-31T19:26:23Z: 30-lei-2023-01..04 (184 Leis of 2023) PUBLISHed (build 678 acts clean).
- 2026-10-31T19:43:48Z: 30-lei-2022-01..03 (146 Leis of 2022) PUBLISHed (build 824 acts clean).
