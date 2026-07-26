#!/usr/bin/env python3
"""
Baut public/assets/img/ aus dem Bildmaterial auf.

Quellenreihenfolge pro Bild:
  1. originals/<wix-id>            -- Originaldatei von Wix, volle Aufloesung
  2. groesste Variante aus dem wget-Mirror

Hintergrund: Wix laedt Bilder per JavaScript nach. Der wget-Mirror hat deshalb
bei einem Teil der Bilder nur den unscharfen Platzhalter (LQIP, z.B. 61x41px
mit blur_2) erwischt. Diese sind fuer den Nachbau unbrauchbar und muessen ueber
tools/fetch-missing-images.sh nachgeladen werden.

Das Skript meldet am Ende, welche Bilder noch Platzhalter sind.

Verwendung:  python3 tools/build-images.py
"""
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MEDIA = os.path.join(ROOT, "miror-alt", "static.wixstatic.com", "media")
ORIGINALS = os.path.join(ROOT, "originals")
DST = os.path.join(ROOT, "public", "assets", "img")

# Wix-Medien-ID -> Zieldateiname (ohne Endung) + Verwendungszweck
MAP = {
    "9d970e_942cbe5236fb4b8fbe3665173da84739~mv2.png":
        ("logo-kopfzeile", "Logo im Seitenkopf, 287x132"),
    "9d970e_ccc93739c7b14e5f9f41a9bca3fa8d51~mv2.png":
        ("logo-hell", "Grosses Logo auf der Startseite, 312x279"),
    "9d970e_54937a25a3f54639a74669d6e73cf288~mv2.png":
        ("instagram", "Instagram-Symbol im Fussbereich, 106x106"),
    "9d970e_23caadb871044f1e9c0f72221f3efea6~mv2.png":
        ("favicon", "Favicon"),
    "11062b_0ff25f13cb54428289ab2905e75f59ea~mv2.jpg":
        ("start-hero", "Startseite, grosses Bild 980x445"),
    "11062b_4d60829cc0024ce3b99663000f52efdb~mv2.jpeg":
        ("start-ueber-uns", "Startseite, Bild bei 'Ueber Uns' 490x397"),
    "2ef2dc_7ceb7be074d543a194047a68ccc64c4a~mv2.jpg":
        ("start-hochformat", "Startseite, Hochformat 490x709"),
    "11062b_880c7b78f2784cb48e182e145a301663~mv2.jpeg":
        ("band-quer", "Querband auf funf Seiten, 619x362"),
    "11062b_16e659636eb643b095afb55c48f8f449~mv2.jpg":
        ("leistungen-1", "Leistungen, linkes Bild 245x436"),
    "11062b_55e976feb9ef42ae87ff8eef2269e582~mv2.jpg":
        ("leistungen-2", "Leistungen, rechtes Bild 245x436"),
    "11062b_3b0b289dbe5448a088a870b81290b4fc~mv2.jpg":
        ("kontakt-hunde", "Kontakt, 'Dog Friends' 510x340"),
    "9d970e_4171dcf38b454e389f119377c2543260~mv2.jpg":
        ("pferdekremierung", "Pferdekremierung, 720x391"),
    "9d970e_eab4cd8ba69d4859919ff5192b7dffc7~mv2.jpg":
        ("tierurnen", "Tierurnen, 572x238"),
}


def variants(media_id):
    """Alle heruntergeladenen Varianten einer Wix-Medien-ID, groesste zuerst."""
    base = os.path.join(MEDIA, media_id)
    if not os.path.isdir(base):
        return []
    found = []
    for dirpath, _, files in os.walk(base):
        for f in files:
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, base)
            w = re.search(r"w_(\d+)", rel)
            blur = "blur_" in rel
            found.append({
                "path": p,
                "width": int(w.group(1)) if w else 0,
                "blur": blur,
                "size": os.path.getsize(p),
            })
    # Nicht-unscharfe zuerst, dann nach Breite
    found.sort(key=lambda v: (v["blur"], -v["width"]))
    return found


def main():
    os.makedirs(DST, exist_ok=True)
    manifest = []
    placeholders = []

    for media_id, (name, purpose) in sorted(MAP.items()):
        ext = os.path.splitext(media_id.split("~")[0])[1] or ".png"
        ext = "." + media_id.rsplit(".", 1)[-1]
        target = os.path.join(DST, name + ext)

        orig = os.path.join(ORIGINALS, media_id)
        if os.path.exists(orig) and os.path.getsize(orig) > 5000:
            shutil.copy2(orig, target)
            manifest.append((name + ext, "Original", os.path.getsize(target), purpose))
            continue

        vs = variants(media_id)
        if not vs:
            print(f"  !! keine Datei fuer {media_id}", file=sys.stderr)
            continue
        best = vs[0]
        shutil.copy2(best["path"], target)
        kind = f"Platzhalter w_{best['width']} (unscharf)" if best["blur"] \
            else f"Mirror w_{best['width']}"
        manifest.append((name + ext, kind, os.path.getsize(target), purpose))
        if best["blur"]:
            placeholders.append((name + ext, media_id, purpose))

    w = max(len(m[0]) for m in manifest)
    print(f"{'Datei':<{w}}  {'Quelle':<28}  {'Groesse':>9}  Verwendung")
    print("-" * (w + 60))
    for f, kind, size, purpose in manifest:
        print(f"{f:<{w}}  {kind:<28}  {size:>8,}B  {purpose}")

    if placeholders:
        print()
        print(f"ACHTUNG: {len(placeholders)} Bild(er) sind noch unscharfe Platzhalter.")
        print("Behebung:  bash tools/fetch-missing-images.sh")
        print("Danach:    python3 tools/build-images.py")
        for f, mid, purpose in placeholders:
            print(f"   - {f}  ({purpose})")
        return 1
    print("\nAlle Bilder liegen in brauchbarer Aufloesung vor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
