#!/usr/bin/env python3
"""
Setzt im Mobil-Spiegel die Schriftverweise auf die lokalen Dateien.

Warum das noetig ist: der Desktop-Spiegel wurde mit wget gezogen, das alle
Verweise auf lokale Pfade umgeschrieben hat. Der Mobil-Spiegel entstand mit
curl, dort stehen die Verweise noch so, wie Wix sie ausliefert:

    //static.parastorage.com/fonts/v2/.../avenir-lt-w01_35-light.woff2

Beim Messen wird der Spiegel ohne Netz gerendert. Ohne erreichbare Schriften
weicht der Browser auf eine Ersatzschrift aus, und deren Metriken sind andere:
eine Zeile mit line-height:normal wurde dadurch 20px statt 26px hoch. Der
Vergleich meldete Abweichungen, die es in Wirklichkeit nicht gibt.

Dieses Skript stellt denselben Zustand her, den wget beim Desktop-Spiegel
erzeugt hat. Am Inhalt aendert sich nichts, nur die Verweise.

Verwendung:  python3 tools/fix-mobile-mirror.py
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOBIL = os.path.join(ROOT, "miror-mobile", "www.tierbestattung-memoria.de")

# Die Schriftdateien liegen beim Desktop-Spiegel. Von den Mobilseiten aus
# gesehen also zwei Ebenen hoch und dort hinein.
ZIEL = "../../miror-alt/static.parastorage.com/"


def main():
    dateien = sorted(glob.glob(os.path.join(MOBIL, "*.html")))
    if not dateien:
        print(f"keine Seiten in {MOBIL}", file=sys.stderr)
        return 1

    gesamt = 0
    for pfad in dateien:
        text = open(pfad, encoding="utf-8", errors="replace").read()
        neu, n = re.subn(r"(?:https?:)?//static\.parastorage\.com/", ZIEL, text)
        if n:
            open(pfad, "w", encoding="utf-8").write(neu)
            gesamt += n
        print(f"  {os.path.basename(pfad):26} {n} Verweis(e)")

    print()
    if gesamt:
        print(f"{gesamt} Schriftverweise auf lokale Dateien gesetzt.")
    else:
        print("Nichts zu tun — die Verweise zeigen bereits lokal.")

    # Gegenprobe: zeigt mindestens ein Verweis auf eine Datei, die es gibt?
    probe = open(dateien[0], encoding="utf-8", errors="replace").read()
    m = re.search(r"url\('(\.\./\.\./miror-alt/[^']+\.woff2)'\)", probe)
    if m:
        p = os.path.normpath(os.path.join(MOBIL, m.group(1)))
        print("Stichprobe:", "gefunden" if os.path.exists(p) else "FEHLT", m.group(1)[-46:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
