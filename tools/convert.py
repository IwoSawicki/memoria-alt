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

# Mobilbetrieb muss feststehen, bevor original.py geladen wird — dort wird der
# Spiegel aus der Umgebungsvariablen MIRROR gelesen.
MOBIL = "--mobile" in sys.argv
if MOBIL:
    os.environ.setdefault("MIRROR", "miror-mobile")

# Seiten der Mobilfassung liegen in public/m/. Von dort aus fuehrt ein
# Verzeichnis nach oben zu den gemeinsamen Dateien.
PREFIX = "../" if MOBIL else ""
AUSGABE = os.path.join(ROOT, "public", "m") if MOBIL else os.path.join(ROOT, "public")

import importlib.util


def _load(name, fname):
    s = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


INS = _load("original_mod", "original.py")
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


SEITEN_PFAD = {
    "index.html": "/",
    "leistungen.html": "/leistungen",
    "preise.html": "/preise",
    "tierurnen-andenken.html": "/tierurnen-andenken",
    "pferdekremierung.html": "/pferdekremierung",
    "kontakt.html": "/kontakt",
    "anfahrt.html": "/anfahrt",
}


def link_umschreiben(href):
    """Interne Verweise auf die Adressform der Live-Seite bringen.

    wget hat beim Spiegeln aus /leistungen ein leistungen.html gemacht.
    Die Live-Seite benutzt aber Adressen ohne Endung, und genau die stehen
    in Suchmaschinen und in fremden Verlinkungen. Also zurueckdrehen.
    """
    if href in SEITEN_PFAD:
        return SEITEN_PFAD[href]
    if href.startswith("_files/"):
        return "/" + href
    return href


def local_image(src):
    """Wix-Bild-URL -> lokaler Dateiname."""
    for mid, fname in MEDIA_TO_FILE.items():
        if mid in src:
            return PREFIX + "assets/img/" + fname
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
    for datei, ziel in SEITEN_PFAD.items():
        s = s.replace(f'href="{datei}"', f'href="{ziel}"')
    s = re.sub(r'href="(_files/[^"]+)"', r'href="/\1"', s)
    # Einzige inhaltliche Korrektur am Original: auf der Kontaktseite steht im
    # Verweisziel eine Domain mit doppelter Endung
    # (mailto:info@tierbestattung-memoria.de.de). Der sichtbare Text ist
    # richtig, nur das Ziel ist falsch — Anfragen darueber kommen nie an.
    # Am Aussehen aendert die Korrektur nichts.
    s = s.replace("mailto:info@tierbestattung-memoria.de.de",
                  "mailto:info@tierbestattung-memoria.de")
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
    if "row" in d:
        parts.append(f'grid-row:{d["row"]}')
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
        # Innenhoehe der Formularfelder (Wix: --inputHeight)
        self.input_heights = dict(
            re.findall(r"#(comp-[\w]+)\{[^}]*--inputHeight:\s*([\d.]+px)", self.html))
        # Schrift der Feldbeschriftung (Wix: --fntlbl). In der Mobilfassung
        # ist sie eine Spur groesser als in der Desktop-Fassung.
        self.label_fonts = dict(
            re.findall(r"#(comp-[\w]+)\{[^}]*--fntlbl:\s*(normal[^;]+)", self.html))
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
        if "wixui-google-map" in c:
            return "map"
        if "wixui-form" in c or n.tag == "form":
            return "form"
        if "wixui-text-input" in c:
            return "text-input"
        if "wixui-text-box" in c:
            return "text-box"
        if "wixui-checkbox" in c:
            return "checkbox"
        # Nur direkte Kinder pruefen: sonst gilt jeder Container, der den
        # Knopf irgendwo unter sich hat, selbst als Knopf.
        if n.tag == "div" and any(ch.tag == "button" and "wixui-button" in ch.attrs.get("class", "")
                                  for ch in n.children):
            return "submit"
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
        gsp = self.spec.get(cid + "inlineContent", {})
        cbits = []
        if gsp.get("gridMinHeight"):
            cbits.append(f'min-height:{gsp["gridMinHeight"]}')
        if gsp.get("gridRows"):
            cbits.append(f'grid-template-rows:{gsp["gridRows"]}')
        if gsp.get("gridMarginTop"):
            cbits.append(f'margin-top:{gsp["gridMarginTop"]}')
        if gsp.get("gridMarginBottom"):
            cbits.append(f'margin-bottom:{gsp["gridMarginBottom"]}')
        cstyle = f' style="{"; ".join(cbits)}"' if cbits else ""
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
        if mh.get("gridRows"):
            bits2.append(f'grid-template-rows:{mh["gridRows"]}')
        if mh.get("gridMarginTop"):
            bits2.append(f'margin-top:{mh["gridMarginTop"]}')
        if mh.get("gridMarginBottom"):
            bits2.append(f'margin-bottom:{mh["gridMarginBottom"]}')
        cstyle = f' style="{"; ".join(bits2)}"' if bits2 else ""
        body = self.emit_children(content, depth + 2) if content is not None else ""
        if body.strip():
            inner.append(f'<div class="col__content"{cstyle}>\n{body}\n</div>')
        else:
            inner.append(f'<div class="col__content"{cstyle}></div>')
        return (f'<div class="col" style="{"; ".join(bits)}">\n'
                + "\n".join(indent(i, 4) for i in inner)
                + "\n</div>")

    def im_formular(self, n):
        """Liegt der Block unmittelbar im Formularcontainer?

        Dort steht im Original nur die Bestaetigungsmeldung. Wix blendet sie
        per JavaScript aus und erst nach dem Absenden ein — im gespiegelten
        HTML ist sie deshalb faelschlich sichtbar.
        """
        for a in ancestors(n):
            if self.kind(a) == "form":
                return True
            if self.kind(a) in ("column", "section", "strip"):
                return False
        return False

    def emit_richtext(self, n, depth):
        cid = n.attrs.get("id", "")
        inner = clean_rich(raw_html(self.html, cid))
        rmh = self.spec.get(cid, {}).get("richMinHeight")
        extra = f"--min-height:{rmh}" if rmh else ""
        style = style_vars(self.spec, cid, extra)
        klass = "mesh rt form__danke" if self.im_formular(n) else "mesh rt"
        return (f'<div data-comp="{cid}" class="{klass}" style="{style}">\n'
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
            href = link_umschreiben(a.attrs.get("href", ""))
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
        href = link_umschreiben(a.attrs.get("href", ""))
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
            href = link_umschreiben(a.attrs.get("href", ""))
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

    # -- Formular --------------------------------------------------
    #
    # Das Original verschickt ueber Wix' eigenes Backend. Das faellt mit dem
    # Abo weg, deshalb laeuft der Versand jetzt ueber FormSubmit.co.
    # Aussehen, Feldreihenfolge und Beschriftungen bleiben unveraendert.

    FORM_ZIEL = "https://formsubmit.co/info@tierbestattung-memoria.de"

    def emit_form(self, n, depth):
        cid = n.attrs.get("id", "")
        content = self.content_of(n)
        felder = self.emit_children(content, depth + 1) if content is not None else ""
        style = style_vars(self.spec, cid)
        return (
            f'<div data-comp="{cid}" class="mesh" style="{style}">\n'
            f'    <form class="form" action="{self.FORM_ZIEL}" method="POST">\n'
            f'        <!-- Steuerfelder von FormSubmit. Werden nicht mitgeschickt,\n'
            f'             sondern vom Dienst ausgewertet. -->\n'
            f'        <input type="hidden" name="_subject" value="Neue Nachricht ueber tierbestattung-memoria.de">\n'
            f'        <input type="hidden" name="_template" value="table">\n'
            f'        <input type="hidden" name="_captcha" value="false">\n'
            f'        <input type="hidden" name="_next" value="https://www.tierbestattung-memoria.de/kontakt?gesendet=1">\n'
            f'        <input type="text" name="_honey" class="honey" tabindex="-1" autocomplete="off">\n'
            f'{indent(felder, 8)}\n'
            f'    </form>\n</div>')

    def feld_variablen(self, cid):
        """Innenhoehe und Beschriftungsschrift eines Formularfelds."""
        teile = []
        ih = self.input_heights.get(cid)
        if ih:
            teile.append(f"--eingabe-hoehe:{ih}")
        lf = self.label_fonts.get(cid)
        if lf:
            teile.append(f"--beschriftung:{lf.strip()}")
        return "; ".join(teile)

    def _label_von(self, n, klasse):
        for el in n.find_all(lambda x: klasse in x.attrs.get("class", "")):
            return el.text.strip()
        return ""

    def emit_text_input(self, n, depth):
        cid = n.attrs.get("id", "")
        label = self._label_von(n, "wixui-text-input__label")
        feld = None
        for i in n.find_all(lambda x: x.tag == "input"):
            feld = i
            break
        name = (feld.attrs.get("name") if feld else "") or cid
        pflicht = feld is not None and "required" in feld.attrs
        maxlen = feld.attrs.get("maxLength") or feld.attrs.get("maxlength") if feld else None
        typ = "text"
        if name.lower() in ("email", "e-mail"):
            typ = "email"
        elif name.lower() in ("fon", "telefon", "phone"):
            typ = "tel"
        attrs = [f'type="{typ}"', f'name="{H.escape(name)}"', f'id="feld-{cid}"',
                 'class="field__input"', 'autocomplete="off"']
        if maxlen:
            attrs.append(f'maxlength="{maxlen}"')
        if pflicht:
            attrs.append("required")
        extra = self.feld_variablen(cid)
        style = style_vars(self.spec, cid, extra)
        return (f'<div data-comp="{cid}" class="mesh field" style="{style}">\n'
                f'    <label class="field__label" for="feld-{cid}">{H.escape(label)}</label>\n'
                f'    <div class="field__box"><input {" ".join(attrs)}></div>\n</div>')

    def emit_text_box(self, n, depth):
        cid = n.attrs.get("id", "")
        label = self._label_von(n, "wixui-text-box__label")
        extra = self.feld_variablen(cid)
        style = style_vars(self.spec, cid, extra)
        return (f'<div data-comp="{cid}" class="mesh field" style="{style}">\n'
                f'    <label class="field__label" for="feld-{cid}">{H.escape(label)}</label>\n'
                f'    <textarea name="Nachricht" id="feld-{cid}" class="field__textarea"></textarea>\n'
                f'</div>')

    def emit_checkbox(self, n, depth):
        cid = n.attrs.get("id", "")
        text = ""
        for el in n.find_all(lambda x: x.attrs.get("data-testid") == "text"):
            text = el.text.strip()
            break
        # Der Hinweis verweist im Original auf die Datenschutzerklaerung.
        beschriftung = H.escape(text)
        for wort in ("Datenschutzerkl&auml;rung", "Datenschutzerkl\u00e4rung"):
            if wort in beschriftung:
                beschriftung = beschriftung.replace(
                    wort, '<a href="/anfahrt">' + wort + "</a>", 1)
                break
        style = style_vars(self.spec, cid)
        return ('<div data-comp="' + cid + '" class="mesh" style="' + style + '">\n'
                '    <label class="check">\n'
                '        <input type="checkbox" name="Datenschutz zur Kenntnis genommen"'
                ' value="ja" class="check__input" required>\n'
                '        <span class="check__label">' + beschriftung + '</span>\n'
                '    </label>\n</div>')

    def emit_submit(self, n, depth):
        cid = n.attrs.get("id", "")
        label = ""
        for b in n.find_all(lambda x: "wixui-button__label" in x.attrs.get("class", "")):
            label = b.text.strip()
            break
        style = style_vars(self.spec, cid)
        return (f'<div data-comp="{cid}" class="mesh" style="{style}">\n'
                f'    <button type="submit" class="submit">{H.escape(label)}</button>\n</div>')

    def emit_map(self, n, depth):
        """Die Karte auf der Kontaktseite.

        Im Original liefert Wix eine eingebettete Google-Karte. Der Kasten ist
        470px hoch und laeuft ueber die volle Breite. Nachgebaut mit dem
        klassischen Google-Maps-Einbettungslink, der ohne Schluessel auskommt.
        """
        cid = n.attrs.get("id", "")
        d = self.spec.get(cid, {})
        bits = []
        for k in ("mt", "mb"):
            if d.get(k) and d[k] != "0px":
                bits.append(f"--{k}:{d[k]}")
        if d.get("h"):
            bits.append(f'--karte-hoehe:{d["h"]}')
        adresse = "Memoria Tierbestattung GmbH, Konrad-Zuse-Str. 3, 69514 Laudenbach"
        style = "; ".join(bits)
        return (f'<div data-comp="{cid}" class="karte" style="{style}">\n'
                f'    <iframe title="Karte: {adresse}" loading="lazy"\n'
                f'            referrerpolicy="no-referrer-when-downgrade"\n'
                f'            src="https://maps.google.com/maps?q='
                f'Konrad-Zuse-Str.+3,+69514+Laudenbach&amp;z=15&amp;output=embed"></iframe>\n'
                f'</div>')

    def emit_generic(self, n, depth):
        """Container ohne eigene Wix-Klasse, der aber eine Position hat.

        Ohne diesen Zweig ginge seine Positionsangabe verloren und der
        Inhalt rutschte an den linken Rand.
        """
        cid = n.attrs.get("id", "")
        content = self.content_of(n)
        body = self.emit_children(content, depth + 1) if content is not None else ""
        style = style_vars(self.spec, cid)
        return (f'<div data-comp="{cid}" class="mesh" style="{style}">\n'
                f'    <div class="box__content">\n{indent(body, 4)}\n    </div>\n</div>')

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
        if k == "map":
            return self.emit_map(n, depth)
        if k == "form":
            return self.emit_form(n, depth)
        if k == "text-input":
            return self.emit_text_input(n, depth)
        if k == "text-box":
            return self.emit_text_box(n, depth)
        if k == "checkbox":
            return self.emit_checkbox(n, depth)
        if k == "submit":
            return self.emit_submit(n, depth)
        # Container ohne eigene Wix-Klasse: wenn er eine eigene Position hat,
        # muss er erhalten bleiben, sonst verliert sein Inhalt den Bezug.
        cid = n.attrs.get("id", "")
        d = self.spec.get(cid, {})
        if cid and self.content_of(n) is not None and ("c" in d or "ml" in d):
            return self.emit_generic(n, depth)
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
        kopf = f'<header class="header">\n{body}\n'
        if MOBIL:
            kopf += indent(self.emit_menue_knopf(), 4) + "\n"
        kopf += "</header>"
        if MOBIL:
            kopf += "\n\n" + self.emit_menue()
        return kopf

    def emit_menue_knopf(self):
        """Der Klapp-Schalter im Kopfbereich der Mobilfassung."""
        style = style_vars(self.spec, "MENU_AS_CONTAINER_TOGGLE")
        return (f'<button type="button" class="mesh menue-knopf" data-comp="MENU_AS_CONTAINER_TOGGLE"\n'
                f'        style="{style}" aria-label="Navigationsmenü öffnen"\n'
                f'        aria-expanded="false" aria-controls="menue">\n'
                f'    <span class="menue-knopf__striche">'
                f'<span></span><span></span><span></span></span>\n'
                f'</button>')

    def emit_menue(self):
        """Das aufklappbare Menue der Mobilfassung.

        Wix blendet es per JavaScript ein; im gespiegelten HTML ist es
        deshalb unsichtbar und laesst sich nicht gegen den Spiegel messen.
        Masse, Schrift und Farben stammen aber aus dessen CSS: Flaeche
        320px breit in var(--color_11), darueber eine Abdunklung aus
        var(--color_37) mit 60 % Deckkraft, Eintraege 50px hoch in
        var(--font_7), mittig, Farbe var(--color_15).
        """
        eintraege = []
        for href, label, aktuell in self.menue_punkte():
            markiert = " is-current" if aktuell else ""
            eintraege.append(f'<li><a class="menue__link{markiert}" href="{H.escape(href)}">'
                             f'{H.escape(label)}</a></li>')
        style = style_vars(self.spec, "MENU_AS_CONTAINER_EXPANDABLE_MENU")
        lis = "\n".join(indent(e, 12) for e in eintraege)
        return (f'<div class="menue" id="menue" hidden>\n'
                f'    <div class="menue__flaeche">\n'
                f'        <nav class="mesh menue__liste" aria-label="Site" style="{style}">\n'
                f'            <ul>\n{lis}\n            </ul>\n'
                f'        </nav>\n'
                f'    </div>\n</div>')

    def menue_punkte(self):
        """Die Menuepunkte aus dem Spiegel, in Originalreihenfolge."""
        raus = []
        frag = INS.find_subtree(INS.body_dom(self.html), "MENU_AS_CONTAINER")
        if frag is None:
            return raus
        for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', frag, re.S):
            href = m.group(1)
            label = H.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
            if not label:
                continue
            # Absolute Adressen der eigenen Domain auf Pfade kuerzen
            href = re.sub(r"^https?://www\.tierbestattung-memoria\.de", "", href) or "/"
            raus.append((href, label, href == self.pfad(self.page)))
        return raus

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

    # Zuordnung Dateiname -> Pfad auf der Live-Seite. Die Originalseite
    # arbeitet mit Adressen ohne Endung (og:url zeigt /kontakt, nicht
    # /kontakt.html). Das wird uebernommen, damit bestehende Links und
    # Suchmaschinen-Eintraege weiter stimmen.
    BASIS_URL = "https://www.tierbestattung-memoria.de"

    def pfad(self, seite):
        return "/" if seite == "index" else "/" + seite

    def viewport(self):
        """Die Mobilfassung bringt ihre eigene Angabe mit (width=320)."""
        m = re.search(r'<meta name="viewport"[^>]*content="([^"]*)"', self.html)
        return m.group(1) if m else "width=320, user-scalable=yes"

    def head(self):
        braucht_formular = "wixui-form" in self.html
        form_css = (f'<link rel="stylesheet" href="{PREFIX}assets/css/form.css">\n'
                    if braucht_formular else "")

        def meta(muster, standard=""):
            m = re.search(muster, self.html, re.S)
            return m.group(1).strip() if m else standard

        titel = meta(r"<title>(.*?)</title>")
        beschreibung = meta(r'<meta name="description" content="(.*?)"')
        og_titel = meta(r'<meta property="og:title" content="(.*?)"', titel)
        og_besch = meta(r'<meta property="og:description" content="(.*?)"', beschreibung)
        # Im Original steht hier "My Site 2" — ein Wix-Standardwert, den die
        # Seite nie ersetzt bekommen hat. Auf der Seite selbst unsichtbar,
        # erscheint aber als Absender, wenn jemand einen Link teilt.
        # Deshalb bewusst korrigiert.
        og_seite = "Memoria Tierbestattung"
        tw_karte = meta(r'<meta name="twitter:card" content="(.*?)"', "summary_large_image")
        url = self.BASIS_URL + self.pfad(self.page)

        zeilen = [
            "<!DOCTYPE html>", '<html lang="de">', "<head>",
            '<meta charset="utf-8">',
            (f'<meta name="viewport" content="{self.viewport()}">' if MOBIL else
            # Wie im Original. Handys bekommen ueber die Geraeteweiche im
            # nginx die Mobilfassung, dieser Wert gilt also nur fuer
            # Desktop-Rechner und Tablets — dort hat er keine Wirkung.
            '<meta name="viewport" content="width=device-width, initial-scale=1">'),
            f"<title>{titel}</title>",
        ]
        if beschreibung:
            zeilen.append(f'<meta name="description" content="{beschreibung}">')
        zeilen.append(f'<link rel="canonical" href="{url}">')
        zeilen += [
            f'<meta property="og:title" content="{og_titel}">',
        ]
        if og_besch:
            zeilen.append(f'<meta property="og:description" content="{og_besch}">')
        zeilen += [
            f'<meta property="og:url" content="{url}">',
            f'<meta property="og:site_name" content="{og_seite}">',
            '<meta property="og:type" content="website">',
            f'<meta name="twitter:card" content="{tw_karte}">',
            f'<meta name="twitter:title" content="{og_titel}">',
        ]
        if og_besch:
            zeilen.append(f'<meta name="twitter:description" content="{og_besch}">')
        zeilen += [
            f'<link rel="icon" sizes="192x192" href="{PREFIX}assets/img/favicon.png">',
            f'<link rel="shortcut icon" href="{PREFIX}assets/img/favicon.png">',
            f'<link rel="apple-touch-icon" href="{PREFIX}assets/img/favicon.png">',
            f'<link rel="stylesheet" href="{PREFIX}assets/css/fonts.css">',
            f'<link rel="stylesheet" href="{PREFIX}assets/css/tokens.css">',
            f'<link rel="stylesheet" href="{PREFIX}assets/css/base.css">',
            f'<link rel="stylesheet" href="{PREFIX}assets/css/layout.css">',
        ]
        if MOBIL:
            zeilen.append(f'<link rel="stylesheet" href="{PREFIX}assets/css/mobil.css">')
        kopf = "\n".join(zeilen) + "\n" + form_css
        return kopf + '</head>\n<body>\n<div class="site">'

    def full_page(self):
        skript = (f'\n<script src="{PREFIX}assets/js/menue.js" defer></script>\n'
                  if MOBIL else "")
        return (self.head() + "\n\n"
                + self.emit_header() + "\n\n<main>\n\n"
                + self.run() + "\n\n</main>\n\n"
                + self.emit_footer() + "\n\n</div>\n"
                + skript
                + self.danke_skript()
                + "</body>\n</html>\n")

    def danke_skript(self):
        if "wixui-form" not in self.html:
            return ""
        return (
            "\n<script>\n"
            "// Nach dem Absenden leitet FormSubmit auf diese Seite zurueck und\n"
            "// haengt ?gesendet=1 an. Dann erscheint die Bestaetigung — im\n"
            "// Original uebernimmt das Wix' Formular-Baustein.\n"
            "if (new URLSearchParams(location.search).has('gesendet')) {\n"
            "    document.querySelectorAll('.form__danke')\n"
            "        .forEach(function (el) { el.classList.add('is-visible'); });\n"
            "}\n</script>\n")

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
        os.makedirs(AUSGABE, exist_ok=True)
        ziel = os.path.join(AUSGABE, page + ".html")
        with open(ziel, "w", encoding="utf-8") as f:
            f.write(c.full_page())
        print(f"geschrieben: {os.path.relpath(ziel, ROOT)}")
    else:
        print(c.run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
