#!/usr/bin/env python3
"""
Abschnitts-Report fuer den Wix-Mirror.

Gibt fuer eine Seite (oder einen Abschnitt) alle Komponenten hierarchisch aus,
jeweils mit Position, Groesse, Hintergrund, Schrift und Textinhalt — also genau
den Werten, die fuer den pixelgenauen Nachbau gebraucht werden.

Verwendung:
  python3 tools/report.py <seite> [comp-id]

Beispiel:
  python3 tools/report.py index
  python3 tools/report.py index comp-lbuw0h70
"""
import html as H
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import importlib.util
_spec = importlib.util.spec_from_file_location("original_mod", os.path.join(HERE, "original.py"))
INS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(INS)

# Deklarationen, die fuer das Aussehen zaehlen. Wix-interne Steuervariablen
# (--above-all-in-container usw.) blenden wir aus, sie erzeugen nur Rauschen.
KEEP = re.compile(
    r"^(width|height|min-width|min-height|max-width|max-height|margin|margin-\w+|"
    r"padding|padding-\w+|left|right|top|bottom|position|display|grid-area|"
    r"grid-template-\w+|justify-self|align-self|justify-content|align-items|"
    r"flex|flex-\w+|column-gap|row-gap|gap|background\w*|border\w*|box-shadow|"
    r"color|font|font-\w+|line-height|letter-spacing|text-\w+|opacity|overflow\w*|"
    r"object-fit|object-position|transform|z-index|--bg[\w-]*|--brw\w*|--brd|--rd|"
    r"--shd|--txt\w*|--fnt|--pad|--alpha-\w+|--column-\w+|--margin|--direction|"
    r"--min-height|--height|--width|--content\w+|--trans|--align)$"
)


def load_rules(page):
    h = INS.load(page)
    css = "".join(c for _, c in INS.all_css(h))
    return h, INS.split_rules(css)


def rules_for(rules, comp):
    """Alle Deklarationen, die auf diese Komponenten-id zielen."""
    out = []
    pat = re.compile(r'(?:#|id=")' + re.escape(comp) + r'(?![\w-])')
    mesh = re.compile(r"data-mesh-id=" + re.escape(comp) + r"(?![\w-])")
    for sel, blk in rules:
        if pat.search(sel) or mesh.search(sel):
            out.append((sel, blk))
    return out


def interesting(blk):
    keep = []
    for d in blk.split(";"):
        d = d.strip()
        if not d or ":" not in d:
            continue
        prop = d.split(":", 1)[0].strip()
        if KEEP.match(prop):
            keep.append(d)
    return keep


def text_of(fragment):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", fragment, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = H.unescape(t)
    t = t.replace("​", "")
    return re.sub(r"\s+", " ", t).strip()


def inline_styles(fragment):
    """Inline-style-Attribute im Fragment, die Schrift oder Farbe setzen."""
    found = []
    for m in re.finditer(r'style="([^"]*)"', fragment):
        s = m.group(1).strip()
        if any(k in s for k in ("font", "color", "text-", "letter-", "line-")):
            if s not in found:
                found.append(s)
    return found


def images(fragment):
    out = []
    for m in re.finditer(r'<img[^>]*>', fragment):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        w = re.search(r'width="(\d+)"', tag)
        hh = re.search(r'height="(\d+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        fit = re.search(r'object-fit:\s*([\w-]+)', tag)
        if src:
            name = os.path.basename(src.group(1).split("/v1/")[0])
            out.append({
                "media": name,
                "w": w.group(1) if w else "?",
                "h": hh.group(1) if hh else "?",
                "alt": alt.group(1) if alt else "",
                "fit": fit.group(1) if fit else "",
            })
    return out


def links(fragment):
    out = []
    for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', fragment, re.S):
        label = text_of(m.group(2))
        if label:
            out.append((m.group(1), label[:60]))
    return out


def walk(dom, rules, root_id, depth=0, seen=None):
    if seen is None:
        seen = set()
    frag = INS.find_subtree(dom, root_id)
    if frag is None:
        return
    pad = "  " * depth
    print(f"\n{pad}{'─' * (72 - len(pad))}")
    print(f"{pad}▸ {root_id}")
    for sel, blk in rules_for(rules, root_id):
        keep = interesting(blk)
        if not keep:
            continue
        short = " ".join(sel.split())
        tag = "[grid]" if "gridContainer]" in short and root_id not in short.split(">")[0] else ""
        if "data-mesh-id" in short:
            tag = "[mesh]"
        print(f"{pad}    {tag} {'; '.join(keep)}")

    for im in images(frag[:4000]):
        print(f"{pad}    BILD {im['media']}  {im['w']}x{im['h']}  fit={im['fit']}  alt={im['alt']!r}")
    for href, label in links(frag)[:6]:
        print(f"{pad}    LINK {href} -> {label!r}")
    st = inline_styles(frag)
    if st:
        for s in st[:8]:
            print(f"{pad}    STIL {s}")

    # direkte Kind-Komponenten
    children = []
    for m in re.finditer(r'\bid="(comp-[\w]+)"', frag):
        cid = m.group(1)
        if cid == root_id or cid in seen:
            continue
        children.append(cid)
    # nur echte Nachkommen erster Ebene: alles, was nicht schon in einem
    # frueheren Kind-Subtree steckt
    direct = []
    covered = ""
    for cid in children:
        if cid in covered:
            continue
        sub = INS.find_subtree(frag, cid)
        if sub is None:
            continue
        direct.append(cid)
        covered += sub

    if not direct:
        t = text_of(frag)
        if t:
            print(f"{pad}    TEXT {t[:400]!r}")
        return

    t_own = text_of(frag)
    if t_own and len(direct) == 0:
        print(f"{pad}    TEXT {t_own[:400]!r}")

    for cid in direct:
        seen.add(cid)
        walk(frag, rules, cid, depth + 1, seen)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    page = sys.argv[1]
    h, rules = load_rules(page)
    dom = INS.body_dom(h)
    if len(sys.argv) > 2:
        walk(dom, rules, sys.argv[2])
    else:
        # alle Sections der Seite
        pid = re.search(r'<style id="css_(\w+)">', h)
        for m in re.finditer(r'<section id="(comp-[\w]+)"[^>]*wixui-section', dom):
            walk(dom, rules, m.group(1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
