#!/usr/bin/env python3
"""
Setzt das gelieferte Logo auf die Bildflaeche, die Wix verwendet hat.

Warum das noetig ist: das Logo im Seitenkopf ist ein Hintergrundbild mit
object-fit: cover. Der Kasten ist 287x132 (Seitenverhaeltnis 2,17), das Bild
ist deutlich breiter — also wird links und rechts etwas abgeschnitten. Wie viel,
haengt allein vom Seitenverhaeltnis der Bilddatei ab:

    Wix-Fassung      2180 x 663   Verhaeltnis 3,29   Logo passt fast vollstaendig
    geliefert        1076 x 264   Verhaeltnis 4,08   Logo wird angeschnitten

Der Logo-Inhalt ist in beiden derselbe, die geliefterte Datei hat nur weniger
Rand oben und unten. Dieses Skript legt den Inhalt mittig auf eine Flaeche mit
dem Seitenverhaeltnis der Wix-Fassung, sodass der Zuschnitt wieder genauso
ausfaellt wie im Original.

Die Sollwerte stammen nicht aus einer Schaetzung: der unscharfe Platzhalter im
Mirror ist eine verkleinerte Fassung des Originalbildes und verraet, welchen
Anteil der Flaeche das Logo dort einnimmt.

Verwendung:  python3 tools/logo-rahmen.py
Ergebnis:    bilder-memoria/Logo-rahmen.png
"""
import os
import sys

from PIL import Image

try:
    import pillow_avif  # noqa: F401  (registriert das AVIF-Format)
except ImportError:
    pass

try:
    import numpy as np
except ImportError:
    print("numpy wird gebraucht:  pip install numpy pillow", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

QUELLE = os.path.join(ROOT, "bilder-memoria", "Logo.png")
ZIEL = os.path.join(ROOT, "bilder-memoria", "Logo-rahmen.png")

# Masse der Wix-Fassung, aus dem data-image-info-Attribut der Originalseite
WIX_BREITE, WIX_HOEHE = 2180, 663

# Anteil der Bildbreite, den das Logo in der Wix-Fassung einnimmt.
# Gemessen am unscharfen Platzhalter (72x22) aus dem Mirror.
ANTEIL_BREITE = 0.811


def inhaltsrahmen(im, schwelle=18):
    """Bounding-Box des sichtbaren Inhalts in Pixeln."""
    g = np.asarray(im.convert("L"), dtype=float)
    rand = np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]])
    hintergrund = np.median(rand)
    maske = np.abs(g - hintergrund) > schwelle
    ys, xs = np.where(maske)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def main():
    if not os.path.exists(QUELLE):
        print(f"nicht gefunden: {QUELLE}", file=sys.stderr)
        return 1

    im = Image.open(QUELLE).convert("RGBA")
    rahmen = inhaltsrahmen(im)
    if rahmen is None:
        print("kein Inhalt erkannt", file=sys.stderr)
        return 1

    inhalt = im.crop(rahmen)
    ib, ih = inhalt.size

    # Flaeche so waehlen, dass der Inhalt denselben Breitenanteil einnimmt
    # wie in der Wix-Fassung, bei deren Seitenverhaeltnis.
    breite = round(ib / ANTEIL_BREITE)
    hoehe = round(breite * WIX_HOEHE / WIX_BREITE)

    if hoehe < ih:
        print("Der Inhalt ist hoeher als die errechnete Flaeche — Abbruch,\n"
              "bitte die Werte pruefen.", file=sys.stderr)
        return 1

    # Hintergrundfarbe aus einer Ecke der Vorlage
    hg = im.getpixel((0, 0))

    flaeche = Image.new("RGBA", (breite, hoehe), hg)
    flaeche.paste(inhalt, ((breite - ib) // 2, (hoehe - ih) // 2), inhalt)
    flaeche.save(ZIEL, "PNG", optimize=True)

    print(f"Vorlage           {im.size[0]}x{im.size[1]}  "
          f"Verhaeltnis {im.size[0]/im.size[1]:.3f}")
    print(f"Logo-Inhalt       {ib}x{ih}  bei x{rahmen[0]}..{rahmen[2]}")
    print(f"neue Flaeche      {breite}x{hoehe}  "
          f"Verhaeltnis {breite/hoehe:.3f}   (Wix: {WIX_BREITE/WIX_HOEHE:.3f})")
    print(f"Breitenanteil     {ib/breite:.3f}   (Wix: {ANTEIL_BREITE:.3f})")
    print(f"geschrieben       {os.path.relpath(ZIEL, ROOT)}  "
          f"{os.path.getsize(ZIEL)//1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
