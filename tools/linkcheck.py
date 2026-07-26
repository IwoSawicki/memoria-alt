#!/usr/bin/env python3
"""
Prueft alle Verweise im Nachbau.

Interne Verweise werden so aufgeloest, wie es der nginx im Container tut
(try_files $uri $uri.html $uri/), damit hier auffaellt, was spaeter ins
Leere laufen wuerde. Externe Verweise werden nur aufgelistet, nicht
abgerufen — sie stammen woertlich aus dem Original.

Verwendung:  python3 tools/linkcheck.py
"""
import os
import re
import sys
from collections import defaultdict
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public")


def loest_auf(pfad):
    """Bildet try_files $uri $uri.html $uri/index.html nach."""
    rel = unquote(pfad.lstrip("/"))
    if rel == "":
        rel = "index.html"
    for kandidat in (rel, rel + ".html", os.path.join(rel, "index.html")):
        if os.path.isfile(os.path.join(PUBLIC, kandidat)):
            return kandidat
    return None


def main():
    intern = defaultdict(set)
    extern = defaultdict(set)
    andere = defaultdict(set)
    seiten = sorted(f for f in os.listdir(PUBLIC) if f.endswith(".html"))

    for seite in seiten:
        text = open(os.path.join(PUBLIC, seite), encoding="utf-8").read()
        for m in re.finditer(r'(?:href|src)="([^"]+)"', text):
            u = m.group(1).strip()
            if not u or u.startswith("#"):
                continue
            if u.startswith(("mailto:", "tel:", "data:", "javascript:")):
                andere[u].add(seite)
            elif u.startswith(("http://", "https://", "//")):
                extern[u].add(seite)
            else:
                intern[u].add(seite)

    fehler = []
    print(f"{len(seiten)} Seiten geprueft\n")

    print("Interne Verweise")
    for u in sorted(intern):
        ziel = loest_auf(u if u.startswith("/") else "/" + u)
        status = "ok   " if ziel else "FEHLT"
        if not ziel:
            fehler.append((u, sorted(intern[u])))
        print(f"  {status} {u:34} <- {', '.join(sorted(intern[u]))}")

    print(f"\nExterne Verweise ({len(extern)} verschiedene, nicht abgerufen)")
    for u in sorted(extern):
        gastgeber = urlparse(u).netloc
        print(f"        {gastgeber:34} {u[:70]}")

    print(f"\nSonstige ({len(andere)})")
    for u in sorted(andere):
        print(f"        {u}")

    print()
    if fehler:
        print(f"{len(fehler)} Verweis(e) laufen ins Leere:")
        for u, wo in fehler:
            print(f"  {u}  (auf {', '.join(wo)})")
        return 1
    print("Alle internen Verweise loesen auf.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
