#!/bin/bash
# Private. Parse finished years, then letters check + build/check/audit of every corpus.d part without .PUBLISH;
# writes .PUBLISH for them only when all pass. Usage: bash verify_new.sh
set -u
F=~/Documents/lexifina/scripts/brazil-sao-paulo-city-law
S=~/Documents/lexifina/scripts
cd "$F"
while :; do
  l=$(tail -1 "$LOCALAPPDATA/gitlaw-cpu.log"); c=$(sed -n 's/.*cpu5=\([0-9]*\).*/\1/p' <<<"$l"); r=$(sed -n 's/.*ram=\([0-9]*\).*/\1/p' <<<"$l")
  [ "${c:-0}" -le 90 ] && [ "${r:-0}" -le 85 ] && break; echo "waiting: $l"; sleep 60
done
python -X utf8 parse.py --today 2026-10-31 || exit 1
NEW=$(for p in corpus.d/*.json; do [ -e "${p%.json}.PUBLISH" ] || echo "$p"; done)
[ -z "$NEW" ] && { echo "nothing new"; exit 0; }
echo "new parts: $NEW"
python -X utf8 check_letters.py $NEW || { echo LETTERS FAIL; exit 1; }
rm -rf .tmp-build
GITLAW_VERIFIED_PARTS_ONLY=0 python -X utf8 $S/gitlaw_common/build.py "$F" --repo "$F/.tmp-build" --docs-date 2026-10-31 >build.out 2>&1 || { tail build.out; echo BUILD FAIL; exit 1; }
python -X utf8 $S/gitlaw_common/check.py "$F/.tmp-build" --corpus "$F/corpus.json" >check.out 2>&1
CK=$?
python -X utf8 -c "import json;d=json.load(open('check.out',encoding='utf-8'));print({k:v for k,v in d.items() if k!='details'})" 2>/dev/null || tail -5 check.out
[ $CK -eq 0 ] || { echo CHECK FAIL; exit 1; }
AUD=$(python -X utf8 -c "import sys; sys.path.insert(0, r'$S/gitlaw_common'); import private; from pathlib import Path; print(private.audit_push(Path(r'$F/.tmp-build'), 'HEAD'))")
echo "audit: $AUD"
[ "$AUD" = "[]" ] || { echo AUDIT FAIL; exit 1; }
N=$(python -X utf8 -c "import json;print(json.load(open('check.out',encoding='utf-8')).get('acts','?'))")
T=$(date -u +%Y-%m-%dT%H:%M:%SZ)
for p in $NEW; do echo "Verified $T gitlaw-scraper-dell: check.py 0 mismatches 0 trailer errors ($N acts); check_letters 0 mismatches; audit_push []." > "${p%.json}.PUBLISH"; done
echo "PUBLISHED $T: $NEW"
rm -rf .tmp-build
