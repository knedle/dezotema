#!/usr/bin/env bash
# Synchronizace nových přepisů z projektu dezoletext do wiki/prepisy/.
#
# Princip: deduplikace podle pole "URL:" v přepisu (NE podle názvu souboru).
#   - Re-přepisy téhož videa mají stejnou URL  -> přeskočeny (i kdyby měly _N).
#   - Skutečná další videa téhož dne mají jinou URL -> stažena.
#   - Soubory *_analyza_* nejsou přepisy -> ignorovány.
# Skript pouze KOPÍRUJE (nikdy nemaže). Idempotentní — opakované spuštění je bezpečné.
#
# Použití:  bash sync-prepisy.sh [zdrojový_adresář]
#   výchozí zdroj: e:/docker/dezoletext/output

set -uo pipefail
SRC="${1:-e:/docker/dezoletext/output}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="$SCRIPT_DIR/wiki/prepisy"
DONE="$DEST/done"

if [ ! -d "$SRC" ]; then echo "Zdroj neexistuje: $SRC" >&2; exit 1; fi

url_of(){ grep -m1 '^URL:' "$1" 2>/dev/null | sed -E 's/^URL:[[:space:]]*//; s/[[:space:]]+$//'; }

# 1) Načti URL všeho, co už máme (prepisy/ i done/)
declare -A known
for f in "$DEST"/*.txt "$DONE"/*.txt; do
  [ -e "$f" ] || continue
  u="$(url_of "$f")"; [ -n "$u" ] && known["$u"]=1
done

# 2) Projdi zdroj a kopíruj jen nové URL
copied=0; have=0; dupbatch=0; nourl=0
declare -A seen
for f in "$SRC"/*.txt; do
  [ -e "$f" ] || continue
  b="$(basename "$f")"
  case "$b" in *_analyza_*) continue;; esac
  u="$(url_of "$f")"
  if [ -z "$u" ]; then
    if [ -e "$DEST/$b" ] || [ -e "$DONE/$b" ]; then have=$((have+1)); continue; fi
    cp "$f" "$DEST/$b"; echo "NOVÝ (bez URL): $b"; copied=$((copied+1)); nourl=$((nourl+1)); continue
  fi
  if [ -n "${known[$u]:-}" ]; then have=$((have+1)); continue; fi
  if [ -n "${seen[$u]:-}" ]; then echo "PŘESKOČENO dup. v dávce (= ${seen[$u]}): $b"; dupbatch=$((dupbatch+1)); continue; fi
  cp "$f" "$DEST/$b"; seen["$u"]="$b"; echo "NOVÝ: $b"; copied=$((copied+1))
done

echo "------------------------------------------------------------"
echo "Zkopírováno: $copied  (z toho bez URL: $nourl)"
echo "Už měl (shoda URL):   $have"
echo "Duplicit v dávce:     $dupbatch"
echo "Připraveno v: $DEST"
