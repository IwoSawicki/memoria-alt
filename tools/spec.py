#!/usr/bin/env python3
"""
Extrahiert die Soll-Werte einer Originalseite als flache Liste.

Fuer jede Komponente werden die Werte ausgelesen, die die Position und Groesse
bestimmen — also genau das, was im Nachbau stimmen muss:

    mesh   c/m/l/w/mt/mb/h   Positionsformel des Inhaltsblocks
    grid   min-height        Mindesthoehe eines Spalteninhalts
    col    flex              Entwurfsbreite einer Spalte
    bg     Farbe             Hintergrund einer Spalte oder eines Abschnitts

Diese Datei ist die Referenz, gegen die tools/check.py den Nachbau prueft.

Verwendung:  python3 tools/spec.py <seite>            (Textausgabe)
             python3 tools/spec.py <seite> --json      (maschinenlesbar)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
import importlib.util
_spec = importlib.util.spec_from_file_location("inspect_mod", os.path.join(HERE, "inspect.py"))
INS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(INS)

# Wix schreibt Nullwerte mal als "0px", mal als blankes "0".
LEN = r"(?:0|-?[\d.]+px)"
MESH_RE = re.compile(
    rf"margin:\s*(?P<mt>{LEN})\s+{LEN}\s+(?P<mb>{LEN})\s+"
    r"calc\(\(100% - (?P<c>[\d.]+px)\) \* (?P<m>[\d.]+)\)"
)
LEFT_RE = re.compile(r"(?:^|;)\s*left:\s*(-?[\d.]+px)")
WH_RE = re.compile(r"(?:^|;)\s*width:\s*(?P<w>[\d.]+px);height:\s*(?P<h>[\d.]+px|auto)")
W_RE = re.compile(r"(?:^|;)\s*width:\s*(?P<w>[\d.]+px)\s*(?:;|$)")
MINH_RE = re.compile(r"min-height:\s*([\d.]+px|auto)")
FLEX_RE = re.compile(r"--column-flex:\s*([\d.]+)")
BG_RE = re.compile(r"--bg-overlay-color:\s*([^;]+)")
MB_ONLY = re.compile(r"margin:\s*(?P<mt>[\d.-]+px)\s+[\d.-]+px\s+(?P<mb>[\d.-]+px)")
# Bloecke innerhalb einer Box benutzen keinen berechneten, sondern einen
# einfachen linken Abstand.
MESH_PLAIN_RE = re.compile(
    rf"margin:\s*(?P<mt>{LEN})\s+{LEN}\s+(?P<mb>{LEN})\s+"
    rf"(?P<ml>{LEN})\s*(?:;|$)"
)
BOX_RE = {
    "boxBg": re.compile(r"(?:^|;)--bg:\s*([^;]+)"),
    "boxRadius": re.compile(r"(?:^|;)--rd:\s*([^;]+)"),
    "boxBorderW": re.compile(r"(?:^|;)--brw:\s*([^;]+)"),
    "boxBorderC": re.compile(r"(?:^|;)--brd:\s*([^;]+)"),
    "boxAlpha": re.compile(r"(?:^|;)--alpha-bg:\s*([\d.]+)"),
}


def build(page):
    h = INS.load(page)
    rules = []
    for _, css in INS.all_css(h):
        rules.extend(INS.split_rules(css))

    comps = {}

    def slot(cid):
        return comps.setdefault(cid, {})

    for sel, blk in rules:
        blk1 = " ".join(blk.split())

        # Platzierungsregel eines Inhaltsblocks im Raster des Elternteils.
        # Wiederholungslisten (Repeater) sprechen ihre Eintraege ueber einen
        # Praefix-Selektor an, deshalb beide Schreibweisen beruecksichtigen.
        ziele = [m.group(1) for m in re.finditer(r'>\s*\[id="(comp-[\w]+)"\]', sel)]
        ziele += [m.group(1) for m in re.finditer(r'>\s*\[id\^="(comp-[\w]+__)"\]', sel)]
        for cid in ziele:
            mm = MESH_RE.search(blk1)
            pm = MESH_PLAIN_RE.search(blk1)
            if mm or pm:
                d = slot(cid)
                src = mm or pm
                d["mt"] = "0px" if src.group("mt") == "0" else src.group("mt")
                d["mb"] = "0px" if src.group("mb") == "0" else src.group("mb")
                if mm:
                    d["c"] = mm.group("c")
                    d["m"] = mm.group("m")
                else:
                    ml = pm.group("ml")
                    d["ml"] = "0px" if ml == "0" else ml
                lm = LEFT_RE.search(blk1)
                d["l"] = lm.group(1) if lm else "0px"

        # Mindesthoehe eines Rastercontainers
        mesh = re.search(r"data-mesh-id=([\w-]+)-gridContainer", sel)
        if mesh:
            mh = MINH_RE.search(blk1)
            if mh and mh.group(1) != "auto":
                slot(mesh.group(1))["gridMinHeight"] = mh.group(1)
            rows = re.search(r"grid-template-rows:\s*([^;]+)", blk1)
            if rows:
                slot(mesh.group(1))["gridRows"] = rows.group(1).strip()
            # Wix zieht einzelne Abschnitte per negativem Abstand nach oben.
            gmt = re.search(r"(?:^|;)margin-top:\s*(-?[\d.]+px)", blk1)
            if gmt and gmt.group(1) != "0px":
                slot(mesh.group(1))["gridMarginTop"] = gmt.group(1)

        mesh2 = re.search(r"data-mesh-id=([\w-]+)\]", sel)
        if mesh2 and "gridContainer" not in sel:
            mh = MINH_RE.search(blk1)
            if mh and mh.group(1) != "auto":
                slot(mesh2.group(1))["minHeight"] = mh.group(1)

        # Eigenschaften der Komponente selbst.
        # Nur Regeln, deren Selektor genau die Komponente ist — Regeln wie
        # "#comp-x .icon" beschreiben ein Kindelement und wuerden sonst
        # dessen Groesse faelschlich der Komponente zuschreiben.
        exact = (re.fullmatch(r"\s*#(comp-[\w]+)\s*", sel)
                 or re.fullmatch(r'\s*\[id\^="(comp-[\w]+__)"\]\s*', sel))
        if exact:
            cid = exact.group(1)
            d = slot(cid)
            for key, rx in BOX_RE.items():
                bm = rx.search(blk1)
                if bm:
                    d[key] = bm.group(1).strip()
            # Streifen: Wix ueberschreibt hier die Positionsformel wieder.
            # Fuer sie zaehlen nur die Abstaende oben und unten.
            if "margin-left:auto" in blk1:
                d["kind"] = "strip-inset"
            elif re.search(r"left:0;margin-left:0", blk1):
                d["kind"] = "strip-full"
            wh = WH_RE.search(blk1)
            if wh:
                d["w"] = wh.group("w")
                if wh.group("h") != "auto":
                    d["h"] = wh.group("h")
            else:
                w = W_RE.search(blk1)
                if w and "column-width" not in blk1:
                    d.setdefault("w", w.group("w"))
            fx = FLEX_RE.search(blk1)
            if fx:
                d["flex"] = fx.group(1)
            bg = BG_RE.search(blk1)
            if bg:
                d["bg"] = bg.group(1).strip()
            rm = re.search(r"--min-height:\s*([\d.]+px)", blk1)
            if rm:
                d["richMinHeight"] = rm.group(1)

    # aufraeumen: leere Eintraege raus
    return {k: v for k, v in sorted(comps.items()) if v}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    page = sys.argv[1]
    data = build(page)
    if "--json" in sys.argv:
        print(json.dumps(data, indent=1, ensure_ascii=False))
        return 0
    for cid, d in data.items():
        parts = []
        for k in ("kind", "c", "m", "l", "ml", "w", "h", "mt", "mb", "flex", "bg",
                  "boxBg", "boxAlpha", "boxRadius", "boxBorderW", "boxBorderC",
                  "gridMinHeight", "gridMarginTop", "gridRows", "minHeight",
                  "richMinHeight"):
            if k in d:
                parts.append(f"{k}={d[k]}")
        print(f"{cid:24} {'  '.join(parts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
