#!/usr/bin/env python3
"""
Erzeugt den Seiteninhalt des Nachbaus aus dem Wix-Mirror.

Warum maschinell und nicht von Hand: die Textbloecke der Originalseite tragen
Angaben, die man beim Abschreiben nicht sieht, aber sofort merkt — welche
font_N-Klasse ein Absatz hat (Poppins oder Avenir, 20px oder 56px), ob eine
Leerzeile ein eigener Absatz oder ein <br> im selben Absatz ist, und ob eine
Ueberschrift als <h1> oder als <p> ausgezeichnet ist. All das aendert die
Hoehe des Blocks und verschiebt damit alles darunter.

Der Konverter uebernimmt diese Auszeichnung woertlich und ersetzt nur das
Geruest von Wix durch die schlanken Klassen aus layout.css.

Verwendung:
  python3 tools/convert.py <seite>            gibt den Rumpf aus
  python3 tools/convert.py <seite> --write     schreibt public/<seite>.html
"""
import html as H
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

import importlib.util


def _load(name, fname):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


INS = _load("inspect_mod", "inspect.py")
SPEC = _load("spec_mod", "spec.py")
IMG = _load("img_mod", "build-images.py")

VOID = {"br", "img", "input", "meta", "link", "hr", "source", "area", "col",
        "path", "use", "circle", "rect", "polygon", "ellipse", "line", "stop"}


# ---------------------------------------------------------------- Baum

class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "text")

    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.parent = None
        self.text = ""

    def cls(self):
        return self.attrs.get("class", "").split()

    def has(self, name):
        return name in self.cls()

    def find_all(self, pred):
        out = []
        if pred(self):
            out.append(self)
        for c in self.children:
            out.extend(c.find_all(pred))
        return out


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node("#root")
        self.stack = [self.root]
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
            return
        if self.skip:
            return
        n = Node(tag, dict(attrs))
        n.parent = self.stack[-1]
        self.stack[-1].children.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        if self.skip:
            return
        n = Node(tag, dict(attrs))
        n.parent = self.stack[-1]
        self.stack[-1].children.append(n)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, d):
        if self.skip:
            return
        self.stack[-1].text += d

    def handle_entityref(self, name):
        if not self.skip:
            self.stack[-1].text += "&%s;" % name

    def handle_charref(self, name):
        if not self.skip:
            self.stack[-1].text += "&#%s;" % name


# ---------------------------------------------------------------- Hilfen

MEDIA_TO_FILE = {}
for _mid, (_name, _purpose) in IMG.MAP.items():
    MEDIA_TO_FILE[_mid] = _name + "." + _mid.rsplit(".", 1)[-1]


def local_image(src):
    """Wix-Bild-URL -> lokaler Dateiname."""
    for mid, fname in MEDIA_TO_FILE.items():
        if mid in src:
            return "assets/img/" + fname
    return None


def raw_html(page_html, comp_id):
    """Roh-HTML eines Elements aus dem Mirror, ohne den aeusseren Tag."""
    frag = INS.find_subtree(INS.body_dom(page_html), comp_id)
    if frag is None:
        return ""
    inner = frag[frag.index(">") + 1:]
    return inner[:inner.rindex("<")]


def clean_rich(inner):
    """Wix-Rich-Text auf das Noetige reduzieren.

    Entfernt wird nur, was nachweislich keine Wirkung hat:
    die Marker-Klasse wixui-rich-text__text (im Original ohne CSS-Regel)
    und data-testid. Absatz-Tags, font_N-Klassen, inline-styles, <br> und
    die Zero-Width-Space-Platzhalter bleiben unveraendert.
    """
    s = inner
    s = re.sub(r'\s*class="wixui-rich-text__text"', "", s)
    s = re.sub(r'(class="[^"]*?)\s*wixui-rich-text__text\s*([^"]*")', r"\1\2", s)
    s = re.sub(r'\s*data-testid="[^"]*"', "", s)
    s = re.sub(r'class="\s*"', "", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def style_vars(spec, comp_id, extra=""):
    d = spec.get(comp_id)
    if d is None:
        # Eintraege einer Wiederholungsliste heissen comp-xxx__<schluessel>
        # und werden im Original ueber einen Praefix-Selektor angesprochen.
        for key in spec:
            if key.endswith("__") and comp_id.startswith(key):
                d = spec[key]
                break
    d = d or {}
    parts = []
    for key in ("c", "m", "l", "ml", "w", "h", "mt", "mb"):
        if key in d:
            parts.append(f"--{key}:{d[key]}")
    if extra:
        parts.append(extra)
    return "; ".join(parts)


def bg_style(spec, comp_id):
    bg = spec.get(comp_id, {}).get("bg")
    if not bg or bg == "transparent":
        return ""
    return f"background-color:{bg}"


def indent(text, n):
    pad = " " * n
    return "\n".join(pad + l if l.strip() else l for l in text.split("\n"))


# ---------------------------------------------------------------- Umwandlung

class Converter:
    def __init__(self, page):
        self.page = page
        self.html = INS.load(page)
        self.spec = SPEC.build(page)
        self.fills = dict(re.findall(r"#(comp-[\w]+)\{[^}]*--fill:([^;}]+)", self.html))
        t = Tree()
        t.feed(INS.body_dom(self.html))
        self.root = t.root
        self.out = []

    # -- Erkennung -------------------------------------------------

    def kind(self, n):
        c = n.cls()
        if "wixui-section" in c:
            return "section"
        if "wixui-column-strip" in c:
            return "strip"
        if "wixui-column-strip__column" in c:
            return "column"
        if "wixui-rich-text" in c:
            return "richtext"
        if "wixui-image" in c:
            return "image"
        if "wixui-vector-image" in c:
            return "vector"
        if n.attrs.get("data-semantic-classname") == "button":
            return "button"
        if "wixui-repeater" in c:
            return "repeater"
        if "wixui-repeater__item" in c:
            return "repeater-item"
        # Eine Box erkennt man an ihrem Hintergrund-Kind
        for ch in n.children:
            if "wixui-box" in ch.cls():
                return "box"
        if n.tag == "wix-dropdown-menu":
            return "menu"
        if "wixui-form" in c or n.tag == "form":
            return "form"
        return None

    def content_of(self, n):
        """Der gridContainer eines Containers."""
        for d in n.find_all(lambda x: x.attrs.get("data-testid") == "mesh-container-content"):
            return d
        return None

    def bg_image_of(self, n):
        """Hintergrundbild eines Containers, sofern vorhanden."""
        for lay in n.children:
            if lay.attrs.get("data-hook") == "bgLayers":
                imgs = lay.find_all(lambda x: x.tag == "img")
                if imgs:
                    return imgs[0]
        return None

    # -- Ausgabe ---------------------------------------------------

    def emit_section(self, n, depth):
        cid = n.attrs.get("id", "")
        bg = bg_style(self.spec, cid)
        style = f' style="{bg}"' if bg else ""
        body = self.emit_children(self.content_of(n), depth + 2)
        stacked = self.is_stacked(n)
        klass = "sec__content sec__content--stacked" if stacked else "sec__content"
        gmt = self.spec.get(cid + "inlineContent", {}).get("gridMarginTop")
        cstyle = f' style="margin-top:{gmt}"' if gmt else ""
        note = ""
        if stacked:
            note = ("\n    <!-- Die beiden Streifen liegen im Original in derselben\n"
                    "         Rasterzelle und ueberlappen sich dadurch. -->")
        return (f'<section data-comp="{cid}" class="sec"{style}>{note}\n'
                f'    <div class="{klass}"{cstyle}>\n{body}\n    </div>\n</section>')

    def is_stacked(self, n):
        """Liegen mehrere Streifen in derselben Rasterzeile?"""
        content = self.content_of(n)
        if content is None:
            return False
        areas = []
        for ch in content.children:
            cid = ch.attrs.get("id")
            if not cid:
                continue
            for sel, blk in SPEC.INS.split_rules(
                    "".join(c for _, c in SPEC.INS.all_css(self.html))):
                if f'"{cid}"' in sel and "grid-area" in blk:
                    m = re.search(r"grid-area:([^;]+)", blk)
                    if m:
                        areas.append(m.group(1).strip())
                    break
        return len(areas) > 1 and len(set(areas)) == 1

    def emit_strip(self, n, depth):
        cid = n.attrs.get("id", "")
        kind = self.spec.get(cid, {}).get("kind", "strip-full")
        klass = "strip strip--inset" if kind == "strip-inset" else "strip"
        bits = []
        for k in ("mt", "mb"):
            v = self.spec.get(cid, {}).get(k)
            if v and v != "0px":
                bits.append(f"--{k}:{v}")
        bg = bg_style(self.spec, cid)
        if bg:
            bits.append(bg)
        style = f' style="{"; ".join(bits)}"' if bits else ""
        # Zwischen Streifen und Spalten liegt bei Wix noch ein Wrapper-div.
        # Deshalb ueber alle Nachfahren suchen und die nehmen, deren
        # naechster Streifen-Vorfahre dieser Streifen ist.
        cols = []
        for ch in n.find_all(lambda x: self.kind(x) == "column"):
            if self.nearest_strip(ch) is n:
                cols.append(self.emit_column(ch, depth + 1))
        return (f'<div data-comp="{cid}" class="{klass}"{style}>\n'
                + "\n".join(indent(c, 4) for c in cols)
                + "\n</div>")

    def nearest_strip(self, n):
        for a in ancestors(n):
            if self.kind(a) == "strip":
                return a
        return None

    def emit_column(self, n, depth):
        cid = n.attrs.get("id", "")
        d = self.spec.get(cid, {})
        bits = [f'--flex:{d.get("flex", "1")}']
        bg = bg_style(self.spec, cid)
        if bg:
            bits.append(bg)
        inner = []
        img = self.bg_image_of(n)
        if img is not None:
            src = local_image(img.attrs.get("src", ""))
            alt = img.attrs.get("alt", "")
            w = img.attrs.get("width", "")
            h = img.attrs.get("height", "")
            if src:
                inner.append('<div class="col__bg">\n'
                             f'    <img src="{src}" alt="{H.escape(alt)}" width="{w}" height="{h}">\n'
                             '</div>')
        content = self.content_of(n)
        mh = self.spec.get(cid + "inlineContent", {})
        mh_val = mh.get("gridMinHeight") or mh.get("minHeight")
        bits2 = []
        if mh_val:
            bits2.append(f"--mh:{mh_val}")
        if mh.get("gridMarginTop"):
            bits2.append(f'margin-top:{mh["gridMarginTop"]}')
        cstyle = f' style="{"; ".join(bits2)}"' if bits2 else ""
        body = self.emit_children(content, depth + 2) if content is not None else ""
        if body.strip():
            inner.append(f'<div class="col__content"{cstyle}>\n{body}\n</div>')
        else:
            inner.append(f'<div class="col__content"{cstyle}></div>')
        return (f'<div class="col" style="{"; ".join(bits)}">\n'
                + "\n".join(indent(i, 4) for i in inner)
                + "\n</div>")

    def emit_richtext(self, n, depth):
        cid = n.attrs.get("id", "")
        inner = clean_rich(raw_html(self.html, cid))
        rmh = self.spec.get(cid, {}).get("richMinHeight")
        extra = f"--min-height:{rmh}" if rmh else ""
        style = style_vars(self.spec, cid, extra)
        return (f'<div data-comp="{cid}" class="mesh rt" style="{style}">\n'
                + indent(inner, 4) + "\n</div>")

    def emit_image(self, n, depth):
        cid = n.attrs.get("id", "")
        imgs = n.find_all(lambda x: x.tag == "img")
        if not imgs:
            return ""
        img = imgs[0]
        src = local_image(img.attrs.get("src", ""))
        alt = img.attrs.get("alt", "")
        w = img.attrs.get("width", "")
        h = img.attrs.get("height", "")
        fit = "object-fit:cover"
        links = n.find_all(lambda x: x.tag == "a")
        tag = (f'<img src="{src}" alt="{H.escape(alt)}" width="{w}" height="{h}" '
               f'style="{fit}">')
        if links:
            a = links[0]
            href = a.attrs.get("href", "")
            rel = a.attrs.get("rel", "")
            target = a.attrs.get("target", "")
            extra = (f' target="{target}"' if target else "") + (f' rel="{rel}"' if rel else "")
            tag = f'<a href="{H.escape(href)}"{extra}>\n    {tag}\n</a>'
        style = style_vars(self.spec, cid)
        return (f'<div data-comp="{cid}" class="mesh" style="{style}">\n'
                + indent(tag, 4) + "\n</div>")

    def emit_vector(self, n, depth):
        cid = n.attrs.get("id", "")
        frag = INS.find_subtree(INS.body_dom(self.html), cid)
        m = re.search(r"<svg.*?</svg>", frag or "", re.S)
        if not m:
            return ""
        svg = m.group(0)
        svg = re.sub(r"\s*data-bbox=\"[^\"]*\"", "", svg)
        svg = re.sub(r"\s*preserveAspectRatio=\"[^\"]*\"", "", svg)
        fill = self.fills.get(cid, "currentColor")
        style = style_vars(self.spec, cid, f"--fill:{fill}")
        return (f'<div data-comp="{cid}" class="mesh vector" style="{style}">\n'
                + indent(svg.strip(), 4) + "\n</div>")

    def emit_button(self, n, depth):
        cid = n.attrs.get("id", "")
        links = n.find_all(lambda x: x.tag == "a")
        if not links:
            return ""
        a = links[0]
        href = a.attrs.get("href", "")
        label = ""
        for sp in n.find_all(lambda x: x.tag == "span" and "__label" in x.attrs.get("class", "")):
            label = sp.text
            break
        target = a.attrs.get("target", "")
        rel = a.attrs.get("rel", "")
        aria = a.attrs.get("aria-label", "").strip()
        extra = (f' target="{target}"' if target else "") + (f' rel="{rel}"' if rel else "")
        style = style_vars(self.spec, cid)
        return (f'<div data-comp="{cid}" class="mesh" style="{style}">\n'
                f'    <a class="btn" href="{H.escape(href)}"{extra} aria-label="{H.escape(aria)}">\n'
                f'        <span class="btn__label">{label}</span>\n'
                f'    </a>\n</div>')

    def emit_menu(self, n, depth):
        """Die Hauptnavigation. Der Menuepunkt "More" wird im Original per
        JavaScript ausgeblendet und faellt hier weg."""
        cid = n.attrs.get("id", "")
        items = []
        for li in n.find_all(lambda x: x.tag == "li"):
            if "__more__" in (li.attrs.get("id") or ""):
                continue
            links = [c for c in li.find_all(lambda x: x.tag == "a")]
            if not links:
                continue
            a = links[0]
            href = a.attrs.get("href", "")
            label = ""
            for pp in li.find_all(lambda x: x.tag == "p"):
                label = pp.text.strip()
                break
            aktuell = " is-current" if a.attrs.get("aria-current") == "page" else ""
            cur = ' aria-current="page"' if aktuell else ""
            items.append(f'<li class="nav__item{aktuell}">'
                         f'<a href="{H.escape(href)}"{cur}>'
                         f'<span class="nav__label">{label}</span></a></li>')
        style = style_vars(self.spec, cid)
        lis = "\n".join(indent(i, 8) for i in items)
        return (f'<nav data-comp="{cid}" class="mesh nav" aria-label="Site" style="{style}">\n'
                f'    <ul class="nav__list">\n{lis}\n    </ul>\n</nav>')

    def emit_box(self, n, depth):
        cid = n.attrs.get("id", "")
        d = self.spec.get(cid, {})
        extra = []
        if d.get("boxBg") and d.get("boxAlpha") != "0":
            extra.append(f'--box-bg:{d["boxBg"]}')
        if d.get("boxRadius") and d["boxRadius"] != "0px 0px 0px 0px":
            extra.append(f'--box-radius:{d["boxRadius"]}')
        if d.get("boxBorderW") and d["boxBorderW"] != "0px":
            extra.append(f'--box-border-w:{d["boxBorderW"]}')
            if d.get("boxBorderC"):
                extra.append(f'--box-border-c:{d["boxBorderC"]}')
        style = style_vars(self.spec, cid, "; ".join(extra))
        body = self.emit_children(self.content_of(n), depth + 1)
        return (f'<div data-comp="{cid}" class="mesh box" style="{style}">\n'
                f'    <div class="box__content">\n{indent(body, 4)}\n    </div>\n</div>')

    def emit_repeater(self, n, depth):
        cid = n.attrs.get("id", "")
        items = []
        for it in n.find_all(lambda x: self.kind(x) == "repeater-item"):
            content = self.content_of(it)
            body = self.emit_children(content, depth + 1) if content is not None else ""
            if body.strip():
                items.append(f'<div class="repeater__item">\n{indent(body, 4)}\n</div>')
        style = style_vars(self.spec, cid)
        return (f'<div data-comp="{cid}" class="mesh repeater" style="{style}">\n'
                + "\n".join(indent(i, 4) for i in items) + "\n</div>")

    def emit_children(self, container, depth):
        if container is None:
            return ""
        out = []
        for ch in container.children:
            piece = self.emit_node(ch, depth)
            if piece:
                out.append(indent(piece, 4))
        return "\n".join(out)

    def emit_node(self, n, depth):
        k = self.kind(n)
        if k == "section":
            return self.emit_section(n, depth)
        if k == "strip":
            return self.emit_strip(n, depth)
        if k == "column":
            return self.emit_column(n, depth)
        if k == "richtext":
            return self.emit_richtext(n, depth)
        if k == "image":
            return self.emit_image(n, depth)
        if k == "vector":
            return self.emit_vector(n, depth)
        if k == "button":
            return self.emit_button(n, depth)
        if k == "menu":
            return self.emit_menu(n, depth)
        if k == "box":
            return self.emit_box(n, depth)
        if k == "repeater":
            return self.emit_repeater(n, depth)
        if k == "form":
            return f'<!-- TODO Formular {n.attrs.get("id","")} -->'
        # unbekannter Container: weiter nach unten
        parts = [self.emit_node(c, depth) for c in n.children]
        return "\n".join(p for p in parts if p)

    def region(self, elem_id):
        """Kopf- oder Fussbereich als Baumknoten."""
        for n in self.root.find_all(lambda x: x.attrs.get("id") == elem_id):
            return n
        return None

    def emit_header(self):
        n = self.region("SITE_HEADER")
        if n is None:
            return ""
        content = self.content_of(n)
        body = self.emit_children(content, 0)
        return f'<header class="header">\n{body}\n</header>'

    def emit_footer(self):
        n = self.region("SITE_FOOTER")
        if n is None:
            return ""
        content = self.content_of(n)
        body = self.emit_children(content, 0)
        mh = self.spec.get("SITE_FOOTERinlineContent", {}).get("gridMinHeight", "620px")
        return (f'<footer class="footer">\n'
                f'    <div class="footer__inner" style="min-height:{mh}">\n'
                f'{indent(body, 4)}\n    </div>\n</footer>')

    def head(self):
        t = re.search(r"<title>(.*?)</title>", self.html, re.S)
        d = re.search(r'<meta name="description" content="(.*?)"', self.html, re.S)
        title = t.group(1).strip() if t else ""
        desc = d.group(1).strip() if d else ""
        meta_desc = f'\n<meta name="description" content="{desc}">' if desc else ""
        return (f'<!DOCTYPE html>\n<html lang="de">\n<head>\n'
                f'<meta charset="utf-8">\n'
                f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                f'<title>{title}</title>{meta_desc}\n'
                f'<link rel="icon" href="assets/img/favicon.png">\n'
                f'<link rel="stylesheet" href="assets/css/fonts.css">\n'
                f'<link rel="stylesheet" href="assets/css/tokens.css">\n'
                f'<link rel="stylesheet" href="assets/css/base.css">\n'
                f'<link rel="stylesheet" href="assets/css/layout.css">\n'
                f'</head>\n<body>\n<div class="site">')

    def full_page(self):
        return (self.head() + "\n\n"
                + self.emit_header() + "\n\n<main>\n\n"
                + self.run() + "\n\n</main>\n\n"
                + self.emit_footer() + "\n\n</div>\n</body>\n</html>\n")

    def run(self):
        secs = self.root.find_all(lambda x: self.kind(x) == "section")
        # nur Abschnitte der Seite, nicht aus Kopf-/Fussbereich
        out = []
        for s in secs:
            out.append(self.emit_section(s, 0))
        if not out:
            # Seiten ohne <section>: direkt die Streifen des Seitencontainers
            strips = [x for x in self.root.find_all(lambda y: self.kind(y) == "strip")
                      if not any(self.kind(p) == "section"
                                 for p in ancestors(x))]
            for st in strips:
                if in_header_or_footer(st):
                    continue
                out.append(self.emit_strip(st, 0))
        return "\n\n".join(out)


def ancestors(n):
    p = n.parent
    while p is not None:
        yield p
        p = p.parent


def in_header_or_footer(n):
    for a in ancestors(n):
        if a.tag in ("header", "footer"):
            return True
        if a.attrs.get("id") in ("SITE_HEADER", "SITE_FOOTER"):
            return True
    return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    page = sys.argv[1]
    c = Converter(page)
    if "--write" in sys.argv:
        ziel = os.path.join(ROOT, "public", page + ".html")
        with open(ziel, "w", encoding="utf-8") as f:
            f.write(c.full_page())
        print(f"geschrieben: public/{page}.html")
    else:
        print(c.run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
