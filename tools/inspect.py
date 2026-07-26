#!/usr/bin/env python3
"""
Inspektor fuer den Wix-Mirror.

Zweck: Fuer den pixelgenauen Nachbau muss jeder Wert (Groesse, Abstand, Farbe,
Font) aus dem Original belegt sein. Wix legt sein generiertes CSS als Inline-
<style>-Bloecke in jede Seite. Dieses Tool macht die Werte auslesbar, statt sie
aus Screenshots schaetzen zu muessen.

Verwendung:
  python3 tools/inspect.py css   <seite>            alle CSS-Bloecke der Seite
  python3 tools/inspect.py comp  <seite> <comp-id>  alle Regeln zu einer Komponente
  python3 tools/inspect.py tree  <seite> [wurzel]   DOM-Baum mit ids/classes
  python3 tools/inspect.py dom   <seite> <comp-id>  DOM-Subtree einer Komponente
  python3 tools/inspect.py text  <seite>            reiner Textinhalt
  python3 tools/inspect.py vars  <seite>            Farb-/Font-Variablen

<seite> ist der Dateiname ohne .html, z.B. "index" oder "kontakt".
"""
import re
import sys
import os
import html as H

MIRROR = os.path.join(os.path.dirname(__file__), "..",
                      "miror-alt", "www.tierbestattung-memoria.de")


def load(page):
    p = os.path.join(MIRROR, page if page.endswith(".html") else page + ".html")
    return open(p, encoding="utf-8", errors="replace").read()


def all_css(h):
    """Alle relevanten Style-Bloecke zusammengefasst, ohne @font-face."""
    out = []
    for m in re.finditer(r'<style id="(css_\w+|stylableCss_\w+|compCssMappers_\w+)">(.*?)</style>',
                         h, re.S):
        css = re.sub(r"@font-face\s*\{[^}]*\}", "", m.group(2))
        out.append((m.group(1), css))
    return out


def body_dom(h):
    """SSR-DOM ohne Scripts und Styles."""
    b = h[h.find("<body"):]
    b = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", b, flags=re.S)
    return b


def split_rules(css):
    """Grobe Zerlegung in (selector, block). Reicht fuer Wix' flaches CSS."""
    rules = []
    depth = 0
    buf = ""
    sel = ""
    i = 0
    while i < len(css):
        c = css[i]
        if c == "{":
            depth += 1
            if depth == 1:
                sel = buf.strip()
                buf = ""
                i += 1
                continue
        elif c == "}":
            depth -= 1
            if depth == 0:
                rules.append((sel, buf.strip()))
                buf = ""
                i += 1
                continue
        buf += c
        i += 1
    return rules


def cmd_css(page):
    h = load(page)
    for name, css in all_css(h):
        print(f"\n{'='*70}\n### {name}  ({len(css)} Zeichen)\n{'='*70}")
        for sel, blk in split_rules(css):
            print(f"{sel} {{\n    {blk}\n}}")


def cmd_vars(page):
    h = load(page)
    for name, css in all_css(h):
        for sel, blk in split_rules(css):
            if "--color_" in blk or "--font_" in blk:
                print(f"### {sel}")
                for d in blk.split(";"):
                    d = d.strip()
                    if d.startswith(("--color", "--font", "--site-width")):
                        print("   ", d)
                print()


def cmd_comp(page, comp):
    h = load(page)
    hits = 0
    for name, css in all_css(h):
        for sel, blk in split_rules(css):
            if comp in sel:
                print(f"[{name}] {sel} {{\n    {blk}\n}}\n")
                hits += 1
    if not hits:
        print(f"(keine CSS-Regel enthaelt {comp!r})")


def _tag_iter(dom):
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)([^>]*?)(/?)>", dom):
        yield m


VOID = {"br", "img", "input", "meta", "link", "hr", "source", "path",
        "use", "circle", "rect", "polygon", "stop", "area", "col"}


def cmd_tree(page, root=None, maxdepth=99):
    h = load(page)
    dom = body_dom(h)
    if root:
        s = find_subtree(dom, root)
        if s is None:
            print(f"(Element {root!r} nicht gefunden)")
            return
        dom = s
    depth = 0
    for m in _tag_iter(dom):
        close, tag, attrs, self = m.groups()
        if tag in VOID:
            if not close:
                idm = re.search(r'\bid="([^"]+)"', attrs)
                srcm = re.search(r'\bsrc="([^"]+)"', attrs)
                if idm or srcm:
                    lbl = idm.group(1) if idm else os.path.basename(
                        (srcm.group(1) or "")[:80])
                    print(f"{'  '*depth}<{tag} {lbl}")
            continue
        if close:
            depth = max(0, depth - 1)
            continue
        idm = re.search(r'\bid="([^"]+)"', attrs)
        cm = re.search(r'\bclass="([^"]+)"', attrs)
        tid = re.search(r'data-testid="([^"]+)"', attrs)
        if depth <= maxdepth:
            bits = [f"{'  '*depth}<{tag}"]
            if idm:
                bits.append("#" + idm.group(1))
            if cm:
                bits.append("." + cm.group(1))
            if tid:
                bits.append(f"[{tid.group(1)}]")
            if idm or cm or tid:
                print(" ".join(bits))
        if not self:
            depth += 1


def find_subtree(dom, elem_id):
    """DOM-Ausschnitt ab dem Element mit der gegebenen id."""
    m = re.search(r'<([a-zA-Z][\w-]*)([^>]*\bid="%s"[^>]*)>' % re.escape(elem_id), dom)
    if not m:
        return None
    tag = m.group(1)
    start = m.start()
    i = m.end()
    depth = 1
    while depth > 0:
        nxt = re.search(r"<(/?)%s\b[^>]*?(/?)>" % re.escape(tag), dom[i:])
        if not nxt:
            return dom[start:]
        if nxt.group(1):
            depth -= 1
        elif not nxt.group(2) and tag not in VOID:
            depth += 1
        i += nxt.end()
    return dom[start:i]


def cmd_dom(page, comp):
    h = load(page)
    s = find_subtree(body_dom(h), comp)
    if s is None:
        print(f"(Element {comp!r} nicht gefunden)")
        return
    s = re.sub(r">\s*<", ">\n<", s)
    print(s)


def cmd_text(page):
    h = load(page)
    t = re.sub(r"<[^>]+>", " ", body_dom(h))
    t = H.unescape(t)
    print(re.sub(r"[ \t]+", " ", t).strip())


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    cmd, page = sys.argv[1], sys.argv[2]
    rest = sys.argv[3:]
    fn = {"css": cmd_css, "comp": cmd_comp, "tree": cmd_tree,
          "dom": cmd_dom, "text": cmd_text, "vars": cmd_vars}.get(cmd)
    if not fn:
        print(__doc__)
        return 1
    fn(page, *rest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
