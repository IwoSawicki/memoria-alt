#!/usr/bin/env bash
#
# Holt die Mobilfassung der Originalseite — nur die sieben HTML-Dateien.
#
# Hintergrund: Die Wix-Seite ist nicht responsiv ("isResponsive": false).
# Wix liefert je nach Geraetekennung zwei voellig unterschiedliche Layouts aus.
# Der erste Spiegel lief mit Desktop-Kennung und enthaelt entsprechend kein
# einziges @media-Breakpoint.
#
# Bilder und Schriften werden nicht noch einmal geladen — die liegen bereits
# im Projekt. Es entstehen also nur sieben Dateien, die sich bequem ueber die
# GitHub-Weboberflaeche hochladen lassen.
#
# Aufruf:
#     bash tools/mirror-mobile.sh [adresse]
#
# Ohne Angabe wird https://www.tierbestattung-memoria.de benutzt. Zeigt diese
# Adresse inzwischen auf den Nachbau, hier die Wix-Adresse angeben, etwa:
#
#     bash tools/mirror-mobile.sh https://benutzername.wixsite.com/meine-seite
#
set -uo pipefail
cd "$(dirname "$0")/.."

BASIS="${1:-https://www.tierbestattung-memoria.de}"
BASIS="${BASIS%/}"
OUT="miror-mobile/www.tierbestattung-memoria.de"
mkdir -p "$OUT"

UA="Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"

SEITEN=("" leistungen preise tierurnen-andenken pferdekremierung kontakt anfahrt)

echo "Quelle: $BASIS"
echo "Ziel:   $OUT"
echo

fehler=0
for p in "${SEITEN[@]}"; do
    name="${p:-index}"
    url="$BASIS/$p"
    printf '  %-22s ' "$name.html"
    if command -v curl >/dev/null 2>&1; then
        code=$(curl -sSL -A "$UA" -o "$OUT/$name.html" -w '%{http_code}' "$url" 2>/dev/null)
    else
        wget -q --user-agent="$UA" -O "$OUT/$name.html" "$url" && code=200 || code=000
    fi
    groesse=$(wc -c < "$OUT/$name.html" 2>/dev/null || echo 0)
    if [ "$code" = "200" ] && [ "$groesse" -gt 50000 ]; then
        echo "ok   ($((groesse/1024)) KB)"
    else
        echo "FEHLER (Status $code, $((groesse/1024)) KB)"
        fehler=$((fehler+1))
    fi
    sleep 1
done

echo
if [ "$fehler" -gt 0 ]; then
    echo "$fehler Seite(n) fehlgeschlagen."
    exit 1
fi

# Gegenprobe: ist das wirklich die Mobilfassung?
if grep -q "device-mobile-optimized\|deviceType=Mobile\|formFactor\":\"Mobile" "$OUT/index.html" 2>/dev/null; then
    echo "Mobilfassung erkannt — das ist der richtige Stand."
else
    echo "ACHTUNG: Die geladenen Seiten sehen nicht nach der Mobilfassung aus."
    echo "Moeglicherweise zeigt die Adresse bereits auf den Nachbau."
    echo "Dann die Wix-Adresse angeben:  bash tools/mirror-mobile.sh <adresse>"
    exit 1
fi

echo
echo "Fertig. Diese sieben Dateien ins Repo laden (Ordner miror-mobile/)."
ls -1sh "$OUT"
