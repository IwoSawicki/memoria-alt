#!/usr/bin/env bash
#
# Ein Befehl fuer alles, was noch Netzzugang braucht.
#
# In der Entwicklungsumgebung sind die Wix-Server gesperrt, deshalb konnten
# diese zwei Schritte dort nicht ausgefuehrt werden:
#
#   1. Die Originalbilder nachladen. Der wget-Mirror hat bei 7 von 13 Bildern
#      nur Wix' unscharfe Vorschau erwischt.
#   2. Die Mobilfassung spiegeln. Die Seite ist nicht responsiv, Wix liefert
#      an Handys ein eigenes Layout aus, das im Desktop-Mirror fehlt.
#
# Danach werden alle Seiten neu erzeugt und geprueft.
#
# Ausfuehren im Repo-Wurzelverzeichnis:
#
#     bash tools/morgen.sh
#
set -uo pipefail
cd "$(dirname "$0")/.."

trenner() { printf '\n%s\n%s\n' "──────────────────────────────────────────────────────────" "$1"; }

trenner "1/5  Originalbilder nachladen"
if bash tools/fetch-missing-images.sh; then
    python3 tools/build-images.py || true
else
    echo "   Bilder konnten nicht geladen werden. Kein Netz? Firewall?"
    echo "   Der Nachbau bleibt vorerst bei den unscharfen Platzhaltern."
fi

trenner "2/5  Mobilfassung spiegeln"
if [ -d miror-mobile/www.tierbestattung-memoria.de ]; then
    echo "   liegt bereits vor, wird uebersprungen"
else
    bash tools/mirror-mobile.sh || echo "   fehlgeschlagen, siehe Meldung oben"
fi

trenner "3/5  Seiten neu erzeugen"
for p in index leistungen preise tierurnen-andenken pferdekremierung anfahrt kontakt; do
    python3 tools/convert.py "$p" --write
done

trenner "4/5  Sollwerte pruefen"
python3 tools/check.py

trenner "5/5  Verweise pruefen"
python3 tools/linkcheck.py | tail -5

trenner "Geometrie gegen das Original messen"
if [ -d node_modules/playwright ]; then
    for p in index leistungen preise tierurnen-andenken pferdekremierung anfahrt kontakt; do
        node tools/compare.js "$p" 1440 2>/dev/null | sed -n "4p" | sed "s/^/  $p: /"
    done
else
    echo "  uebersprungen — dafuer einmalig 'npm install playwright' ausfuehren"
fi

trenner "Stand"
python3 - <<'PY'
import glob, os, re
platzhalter = []
for f in glob.glob("public/assets/img/*"):
    if os.path.getsize(f) < 6000 and not f.endswith(("favicon.png",)):
        platzhalter.append(os.path.basename(f))
print("  Bilder:  " + ("alle in voller Aufloesung"
      if not platzhalter else f"{len(platzhalter)} noch Platzhalter: " + ", ".join(platzhalter)))
mobil = os.path.isdir("miror-mobile/www.tierbestattung-memoria.de")
print("  Mobil:   " + ("Mirror liegt vor, Mobilfassung kann gebaut werden"
      if mobil else "Mirror fehlt — Seite laeuft auf dem Handy im Notbehelf (herunterskaliert)"))
vp = open("public/index.html", encoding="utf-8").read()
print("  Viewport: " + (re.search(r'content="width=[^"]*"', vp).group(0)))
PY

printf '\n%s\n' "Wenn oben alles sauber ist:  git add -A && git commit && git push"
