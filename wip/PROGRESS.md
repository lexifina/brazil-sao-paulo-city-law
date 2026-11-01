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
- 2026-10-31T20:12:15Z: 30-lei-2021-01..04 (184 Leis of 2021) PUBLISHed (build 1008 acts clean). Fetch PID 41236 continues (2020 and older, newest first); each finished year needs parse.py + check_letters + build/check/audit before its PUBLISH.
- 2026-10-31T20:34:00Z: 30-lei-2020-01..06 PUBLISHed (build 1286 acts clean, letters 0, audit []). From now on: bash ../world-law/br_city_verify.sh <folder> after each year (also run by br_city_loop.sh).
- ~20:56Z detached loop (world-law/br_city_loops_run.sh sp): each finished year -> br_city_verify.sh -> PUBLISH; when
  fetch PID 41236 exits after "1892 done" the claim is deleted, otherwise kept (check .cache/STOP first).

## Restart (one command) — 2026-11-01
`powershell -NoProfile -ExecutionPolicy Bypass -File ~\Documents\lexifina\scripts\world-law\br_city_resume.ps1`
Idempotent: starts the fetch from cache (one process, >= 3 s, BelowNormal) unless the list is done, it is running, or the
host has a STOP file (never removed by the script: check the host by hand first, log it in SCRAPING-LOG.md); starts the
verify/publish loop (world-law/br_city_<sp|mc>.sh loop -> br_city_loop.sh) unless running. PIDs: fetch.pid, loop.pid.
The loop publishes one year per run, newest first (.verified-years; a failing year goes to .failed-years and is skipped:
retry by hand with `bash world-law/br_city_verify.sh <folder> <year>`). It deletes the claim only when the list is done.
br_city_verify.sh holds a lock (.verify.lock) and builds outside scripts/ (%LOCALAPPDATA%/gitlaw-br-city/<slug>-<pid>).
- Night 10-31/11-01: the fetch ran through 1992 (years-done 2026..1992), then stopped on a transient HTTP 500 on a
  Detalhes page (06:30Z, lei-10959/1991); 09:06Z one check: 200, STOP moved to .cache/STOP.0630Z. The loop failed at
  2019 (21:01Z): two verify runs shared .tmp-build (an earlier loop instance was still alive) -> build/check failures;
  nothing bad was PUBLISHed (2019 parts stayed unpublished). Fixed with the lock + per-run build folder above.
- 09:07Z resumed: fetch PID 48208 (--years 2024-1892, cached years pass without requests; resumes in 1991), loop PID 3008
  draining 2019 -> 1992, one year per PUBLISH batch.
- 2026-11-01 rule (coordinator, after three WAF blocks elsewhere): no stated Crawl-delay -> <= 1 request / 3 s and ~5,000
  requests per host per UTC day; stop for good on any challenge (br_city_get already writes STOP on a challenge page).
  world-law/br_city_get.py Host(..., daily_cap=N) counts the day's requests from requests.jsonl and sleeps to the next
  UTC day at the cap; fetch.py uses daily_cap=5000. 09:28Z restarted via br_city_resume.ps1 (old fetch PID 48208
  stopped): PID 20156. 7,649 requests already on 11-01 (UTC), so it paused at once until 2026-11-02T00:00:05Z, at year
  1989 (2019..1990 fetched). At ~5,000 a day the rest (1989..1892) takes a few more days; the loop keeps publishing
  each finished year meanwhile, and resume.ps1 restarts both after any sleep or reboot.
