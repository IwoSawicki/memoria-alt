#!/usr/bin/env python3
"""
Prueft den Nachbau gegen die Originalwerte.

Jeder Inhaltsblock im Nachbau traegt ein data-comp-Attribut mit der
Komponenten-Kennung aus der Wix-Seite, zum Beispiel:

    <div class="mesh" data-comp="comp-kbae6aww"
         style="--c:490px; --m:0.5; --l:15px; --w:460px; --mt:134px; --mb:28px">

Dieses Skript liest diese Werte aus, holt die Sollwerte aus der Originalseite
(tools/spec.py) und meldet jede Abweichung. Damit kann sich beim Uebertragen
kein Zahlendreher einschleichen, und es faellt auf, wenn ein Block vergessen
wurde.

Verwendung:
  python3 tools/check.py                 alle fertigen Seiten
  python3 tools/check.py index           nur eine Seite
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PUBLIC = os.path.join(ROOT, "public")

import importlib.util
_s = importlib.util.spec_from_file_location("spec_mod", os.path.join(HERE, "spec.py"))
SPEC = importlib.util.module_from_spec(_s)
_s.loader.exec_module(SPEC)

# Nachbau-Datei -> Originalseite
PAGES = {
    "index.html": "index",
    "leistungen.html": "leistungen",
    "preise.html": "preise",
    "tierurnen-andenken.html": "tierurnen-andenken",
    "pferdekremierung.html": "pferdekremierung",
    "kontakt.html": "kontakt",
    "anfahrt.html": "anfahrt",
}

VARS = ("c", "m", "l", "w", "h", "mt", "mb")

# Werte, die im Nachbau weggelassen werden duerfen, weil layout.css
# denselben Vorgabewert setzt.
DEFAULTS = {"mt": "0px", "mb": "0px", "l": "0px"}

# Bei Streifen ueberschreibt Wix die Positionsformel wieder, es zaehlen nur
# die Abstaende oben und unten.
STRIP_VARS = ("mt", "mb")


def norm(v):
    if v is None:
        return None
    v = v.strip()
    if v in ("0", "0px"):
        return "0px"
    # 0.50 == 0.5, 1.0 == 1
    if re.fullmatch(r"[\d.]+", v):
        f = float(v)
        return str(int(f)) if f == int(f) else str(f)
    return v


def parse_build(path):
    """Alle data-comp-Bloecke des Nachbaus mit ihren CSS-Variablen."""
    html = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"<[^>]*\bdata-comp=\"([^\"]+)\"[^>]*>", html):
        tag = m.group(0)
        cid = m.group(1)
        style = re.search(r'style="([^"]*)"', tag)
        vals = {}
        if style:
            for d in style.group(1).split(";"):
                d = d.strip()
                if d.startswith("--") and ":" in d:
                    k, v = d[2:].split(":", 1)
                    vals[k.strip()] = v.strip()
        out[cid] = vals
    return out


def check_page(build_file, orig_page):
    path = os.path.join(PUBLIC, build_file)
    if not os.path.exists(path):
        return None
    want = SPEC.build(orig_page)
    got = parse_build(path)

    problems = []
    checked = 0

    for cid, gvals in sorted(got.items()):
        wvals = want.get(cid)
        if wvals is None:
            problems.append(f"  {cid}: im Original nicht gefunden (Tippfehler in data-comp?)")
            continue
        keys = STRIP_VARS if str(wvals.get("kind", "")).startswith("strip") else VARS
        for key in keys:
            w = norm(wvals.get(key))
            g = norm(gvals.get(key))
            if g is None and key in DEFAULTS and w == DEFAULTS[key]:
                # nicht gesetzt, aber der Vorgabewert stimmt
                checked += 1
                continue
            if w is None and g is None:
                continue
            if w is None:
                # Nachbau setzt einen Wert, den das Original nicht kennt
                if key in ("h",) and g == "auto":
                    continue
                problems.append(f"  {cid}: --{key} ist {g}, das Original setzt hier nichts")
                continue
            if g is None:
                problems.append(f"  {cid}: --{key} fehlt, Original {w}")
                continue
            if w != g:
                problems.append(f"  {cid}: --{key} ist {g}, Original {w}")
            checked += 1

    # Bloecke, die es im Original gibt, im Nachbau aber nicht
    positioned = {c for c, v in want.items()
                  if ("c" in v and "m" in v) or str(v.get("kind", "")).startswith("strip")}
    missing = positioned - set(got)
    # Kopf- und Fussbereich sind auf jeder Seite gleich und werden separat
    # geprueft; hier nur melden, was zur Seite selbst gehoert.
    for cid in sorted(missing):
        problems.append(f"  {cid}: im Nachbau nicht vorhanden (Sollwerte: "
                        + " ".join(f"{k}={want[cid][k]}" for k in VARS if k in want[cid]) + ")")

    return checked, problems


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    total_problems = 0
    any_page = False

    for build_file, orig in PAGES.items():
        if only and orig != only and build_file != only:
            continue
        res = check_page(build_file, orig)
        if res is None:
            continue
        any_page = True
        checked, problems = res
        if problems:
            print(f"\n{build_file}  —  {len(problems)} Abweichung(en), {checked} Werte geprueft")
            for p in problems:
                print(p)
            total_problems += len(problems)
        else:
            print(f"{build_file}  —  in Ordnung ({checked} Werte geprueft)")

    if not any_page:
        print("Keine fertige Seite gefunden.")
        return 0
    print()
    if total_problems:
        print(f"Ergebnis: {total_problems} Abweichung(en).")
        return 1
    print("Ergebnis: keine Abweichungen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
