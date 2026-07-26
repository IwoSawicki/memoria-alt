#!/usr/bin/env bash
# Zieht die Mobile-Variante der Originalseite.
#
# Hintergrund: Die Wix-Seite ist NICHT responsive ("isResponsive": false).
# Wix liefert je nach User-Agent zwei komplett unterschiedliche Layouts aus.
# Der erste Mirror lief mit Desktop-UA und enthaelt entsprechend kein einziges
# @media-Breakpoint. Fuer den pixelgenauen Mobile-Nachbau braucht es einen
# zweiten Durchlauf mit Handy-User-Agent.
#
# Ausfuehren im Repo-Root:  bash tools/mirror-mobile.sh
# Danach:                   git add miror-mobile && git commit && git push

set -euo pipefail

OUT="miror-mobile"
mkdir -p "$OUT"
cd "$OUT"

UA="Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"

DOMAINS="www.tierbestattung-memoria.de,tierbestattung-memoria.de,static.wixstatic.com,static.parastorage.com,siteassets.parastorage.com,fonts.gstatic.com,fonts.googleapis.com"

PAGES=(
  ""
  "leistungen"
  "preise"
  "tierurnen-andenken"
  "pferdekremierung"
  "kontakt"
  "anfahrt"
)

for p in "${PAGES[@]}"; do
  url="https://www.tierbestattung-memoria.de/$p"
  echo "==> $url"
  wget \
    --page-requisites \
    --adjust-extension \
    --convert-links \
    --span-hosts \
    --domains="$DOMAINS" \
    --execute robots=off \
    --user-agent="$UA" \
    --wait=1 --random-wait \
    --restrict-file-names=windows \
    --no-check-certificate \
    --tries=3 --timeout=30 \
    "$url" || echo "   (fehlgeschlagen, weiter)"
done

echo
echo "Fertig. Kontrolle: die HTML-Dateien muessen sich vom Desktop-Mirror unterscheiden."
ls -lh www.tierbestattung-memoria.de/*.html 2>/dev/null || true
