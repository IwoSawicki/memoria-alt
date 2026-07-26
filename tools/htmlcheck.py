#!/usr/bin/env python3
"""
Grundpruefung des erzeugten HTML.

Sucht nach dem, was ein Konverter typischerweise falsch machen kann:
nicht geschlossene Tags, falsch verschachtelte Elemente, doppelte
Kennungen, fehlende Pflichtangaben im Kopf, Reste aus der Entwicklung.

Verwendung:  python3 tools/htmlcheck.py
"""
import os
import re
import sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public")

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
# In SVG wird selbstschliessend geschrieben, das ist in Ordnung.
SVG = {"svg", "path", "g", "circle", "rect", "polygon", "ellipse", "line",
       "polyline", "defs", "use", "stop", "text", "tspan", "clipPath", "mask"}


class Pruefer(HTMLParser):
    def __init__(self, datei):
        super().__init__(convert_charrefs=True)
        self.datei = datei
        self.stapel = []
        self.probleme = []
        self.ids = Counter()
        self.in_svg = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids[d["id"]] += 1
        if tag == "svg":
            self.in_svg += 1
        if tag in VOID:
            return
        if self.in_svg and tag in SVG:
            return
        self.stapel.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        if tag == "svg":
            return
        d = dict(attrs)
        if d.get("id"):
            self.ids[d["id"]] += 1

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        # Erst pruefen, dann den Zaehler senken: sonst gilt </svg> selbst
        # schon als ausserhalb und wuerde faelschlich bemaengelt.
        if self.in_svg and tag in SVG:
            if tag == "svg":
                self.in_svg = max(0, self.in_svg - 1)
            return
        if not self.stapel:
            self.probleme.append(f"Zeile {self.getpos()[0]}: </{tag}> ohne oeffnendes Tag")
            return
        if self.stapel[-1][0] == tag:
            self.stapel.pop()
            return
        # weiter unten im Stapel suchen
        for i in range(len(self.stapel) - 1, -1, -1):
            if self.stapel[i][0] == tag:
                offen = [t for t, _ in self.stapel[i + 1:]]
                self.probleme.append(
                    f"Zeile {self.getpos()[0]}: </{tag}> schliesst, aber "
                    f"{', '.join('<' + o + '>' for o in offen)} ist noch offen")
                del self.stapel[i:]
                return
        self.probleme.append(f"Zeile {self.getpos()[0]}: </{tag}> ohne oeffnendes Tag")


def main():
    seiten = sorted(f for f in os.listdir(PUBLIC) if f.endswith(".html"))
    gesamt = 0

    for seite in seiten:
        pfad = os.path.join(PUBLIC, seite)
        text = open(pfad, encoding="utf-8").read()
        p = Pruefer(seite)
        p.feed(text)
        p.close()

        probleme = list(p.probleme)
        for tag, zeile in p.stapel:
            probleme.append(f"Zeile {zeile}: <{tag}> wird nie geschlossen")
        for kennung, anzahl in p.ids.items():
            if anzahl > 1:
                probleme.append(f'id="{kennung}" kommt {anzahl}x vor')

        # Pflichtangaben im Kopf
        pflicht = [
            (r"<title>[^<]+</title>", "<title>"),
            (r'<meta charset="utf-8">', "charset"),
            (r'<meta name="viewport"', "viewport"),
            (r'<html lang="de">', 'lang="de"'),
        ]
        if seite == "404.html":
            # Eine Fehlerseite bekommt kein canonical, sondern noindex.
            pflicht.append((r'<meta name="robots" content="noindex">', "noindex"))
        else:
            pflicht.append((r'<link rel="canonical"', "canonical"))
        for muster, name in pflicht:
            if not re.search(muster, text):
                probleme.append(f"{name} fehlt")

        # Entwicklungsreste
        for rest in ("TODO", "FIXME", "wixui-", "parastorage", "wixstatic",
                     "data-testid", "undefined"):
            if rest in text:
                anzahl = text.count(rest)
                probleme.append(f"Rest im Markup: {rest!r} ({anzahl}x)")

        if probleme:
            print(f"\n{seite}  —  {len(probleme)} Hinweis(e)")
            for x in probleme:
                print(f"  {x}")
            gesamt += len(probleme)
        else:
            print(f"{seite}  —  in Ordnung")

    print()
    if gesamt:
        print(f"Ergebnis: {gesamt} Hinweis(e).")
        return 1
    print(f"Ergebnis: {len(seiten)} Seiten ohne Beanstandung.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
