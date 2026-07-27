#!/usr/bin/env python3
"""
Baut public/assets/img/ aus dem Bildmaterial auf.

Quellenreihenfolge pro Bild:
  1. originals/<wix-id>            -- unbeschnittenes Original von Wix
  2. bilder-memoria/<datei>        -- vom Kunden geliefert
  3. groesste Variante aus dem wget-Mirror

Warum die Wix-Originale zuerst: die gelieferten Bilder sind bereits auf das
Desktop-Format zugeschnitten. Die Mobilfassung schneidet dieselben Bilder aber
anders zu — aus einem 4:1-Banner wird dort ein hochkantiger Ausschnitt. Dafuer
fehlen dem zugeschnittenen Bild schlicht die Bildpunkte. Wix arbeitet mit den
unbeschnittenen Aufnahmen (etwa 4896x3264) und schneidet je Fassung neu zu —
genau das macht der Nachbau ueber object-fit: cover auch.

Die Originale holt  bash tools/fetch-missing-images.sh

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

# Wie gross eine Bilddatei sein muss, haengt an zwei Dingen: an den Kaesten,
# in denen sie angezeigt wird, und daran, wie das Geraet diese Kaesten auf
# echte Bildpunkte abbildet.
#
#   Desktop: Faktor 2 deckt hochaufloesende Bildschirme ab.
#   Mobil:   Die Mobilfassung rechnet mit einer 320px breiten Flaeche, die das
#            Telefon erst auf die Bildschirmbreite hochskaliert (rund 430
#            Punkte) und dann mit seiner Pixeldichte (bis 3) rendert. Ein
#            320px breiter Kasten braucht damit rund 1290 echte Bildpunkte.
FAKTOR = {"desktop": 2.0, "mobil": 430 / 320 * 3}

# Entscheidend: die Bilder werden mit object-fit: cover angezeigt. Das FUELLT
# den Kasten AUS und schneidet den Ueberstand ab. Eine Datei ist also nur dann
# gross genug, wenn sie in BEIDEN Richtungen reicht. Wer hier mit "ins Format
# einpassen" rechnet, macht die Bilder unscharf — genau das ist schon einmal
# passiert.

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MEDIA = os.path.join(ROOT, "miror-alt", "static.wixstatic.com", "media")
ORIGINALS = os.path.join(ROOT, "originals")
GELIEFERT = os.path.join(ROOT, "bilder-memoria")

# Vom Kunden geliefertes Bild je Platz. Die Zuordnung wurde nicht nach
# Dateinamen geraten, sondern nachgerechnet: die unscharfen Platzhalter aus
# dem Mirror sind verkleinerte Fassungen der echten Bilder, ein Vergleich der
# Miniaturen ergab fuer jeden Platz genau einen eindeutigen Treffer.
#
# Logo.png ist die nach PNG gewandelte Logo.avif. AVIF zeigen aeltere
# iPhones (bis iOS 16.3) nicht an, und das Logo steht auf jeder Seite.
GELIEFERTE_DATEI = {
    # Logo-rahmen.png ist die gelieferte Logo.avif, gewandelt nach PNG und auf
    # die Bildflaeche gesetzt, die Wix verwendet hat — siehe
    # tools/logo-rahmen.py. Ohne das wird das Logo im Kopf angeschnitten.
    "logo-kopfzeile": "Logo-rahmen.png",
    "start-hero": "startseite-banner.jpg",
    "start-hochformat": "startseite-bild1.jpg",
    "start-ueber-uns": "startseite-bild2.jpeg",
    "band-quer": "terminbuchen.jpeg",
    "leistungen-1": "leistungen-1.jpg",
    "leistungen-2": "leistungen-2.jpg",
    "kontakt-hunde": "kontakt.jpg",
    "pferdekremierung": "pferde.jpg",
}
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


def anzeigegroessen():
    """Welche Bildkaesten es gibt, je Wix-Medien-Kennung.

    Wird aus beiden Spiegeln gelesen, nicht geschaetzt: Wix schreibt zu jedem
    Bild ein data-image-info-Attribut mit der Zielgroesse, und die einfachen
    Bildelemente tragen width/height direkt am img-Tag.
    """
    import glob
    import html as _h
    import json

    raus = {}
    for verzeichnis, fassung in ((os.path.join(ROOT, "miror-alt"), "desktop"),
                                 (os.path.join(ROOT, "miror-mobile"), "mobil")):
        muster = os.path.join(verzeichnis, "www.tierbestattung-memoria.de", "*.html")
        for datei in glob.glob(muster):
            text = open(datei, encoding="utf-8", errors="replace").read()

            for m in re.finditer(r'data-image-info="([^"]+)"', text):
                try:
                    d = json.loads(_h.unescape(m.group(1)))
                except ValueError:
                    continue
                uri = d.get("imageData", {}).get("uri")
                tw, th = d.get("targetWidth"), d.get("targetHeight")
                if uri and tw and th:
                    raus.setdefault(uri, []).append((fassung, int(tw), int(th)))

            # Einfache Bildelemente (wixui-image) tragen am img-Tag die
            # NATUERLICHE Groesse, nicht die Anzeigegroesse — auf der
            # Pferdeseite steht dort 1931x1048 fuer einen 720x391-Kasten.
            # Die Anzeigegroesse steht im generierten CSS der Komponente,
            # also dort nachschlagen.
            seite = os.path.splitext(os.path.basename(datei))[0]
            alt_mirror = os.environ.get("MIRROR")
            os.environ["MIRROR"] = os.path.basename(verzeichnis)
            try:
                sollwerte = _spec_modul().build(seite)
            except Exception:
                sollwerte = {}
            finally:
                if alt_mirror is None:
                    os.environ.pop("MIRROR", None)
                else:
                    os.environ["MIRROR"] = alt_mirror

            for m in re.finditer(
                    r'<div id="(comp-\w+)"[^>]*wixui-image.*?</div>', text, re.S):
                comp = m.group(1)
                kennung = re.search(r"([0-9a-f]{6}_[0-9a-f]{32}~mv2\.\w+)", m.group(0))
                d = sollwerte.get(comp, {})
                if kennung and d.get("w") and d.get("h"):
                    raus.setdefault(kennung.group(1), []).append(
                        (fassung, int(float(d["w"][:-2])), int(float(d["h"][:-2]))))
    return raus


def _spec_modul():
    """tools/spec.py nachladen — es liest den Spiegel aus der Umgebung."""
    import importlib.util
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec.py")
    sp = importlib.util.spec_from_file_location("spec_fuer_bilder", pfad)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


_ANZEIGE = None


def verkleinern(pfad, media_id):
    """Bild auf die kleinste Groesse bringen, die ueberall noch scharf ist.

    Gerechnet wird fuer object-fit: cover — die Datei muss in beiden
    Richtungen reichen. Hochgerechnet wird nie: ist die Vorlage schon zu
    klein, bleibt sie wie sie ist.
    """
    global _ANZEIGE
    if _ANZEIGE is None:
        _ANZEIGE = anzeigegroessen()

    faelle = _ANZEIGE.get(media_id)
    if not faelle:
        return None
    try:
        from PIL import Image
    except ImportError:
        return "Pillow fehlt"

    noetig_b = max(round(w * FAKTOR[f]) for f, w, h in faelle)
    noetig_h = max(round(h * FAKTOR[f]) for f, w, h in faelle)

    im = Image.open(pfad)
    vorher = os.path.getsize(pfad)

    # So weit verkleinern, dass beide Richtungen gerade noch reichen.
    skala = max(noetig_b / im.width, noetig_h / im.height)
    if skala >= 1:
        return None                      # Vorlage ist schon knapp oder zu klein

    ziel = (max(1, round(im.width * skala)), max(1, round(im.height * skala)))
    kopie = im.resize(ziel, Image.LANCZOS)
    if im.format == "PNG" or im.mode in ("RGBA", "P", "LA"):
        kopie.save(pfad, "PNG", optimize=True)
    else:
        kopie.save(pfad, "JPEG", quality=85, optimize=True, progressive=True)

    nachher = os.path.getsize(pfad)
    if nachher >= vorher:
        return None
    return (vorher, nachher, ziel, (noetig_b, noetig_h))



    """Bilder werden bewusst NICHT verkleinert.

    Ein frueherer Versuch, hier Ladezeit zu sparen, hat die Bilder unscharf
    gemacht. Der Denkfehler: verkleinert wurde mit thumbnail(), das ein Bild
    in einen Rahmen HINEINPASST. Angezeigt werden die Bilder aber mit
    object-fit: cover, das den Rahmen AUSFUELLT und den Rest abschneidet.
    Fuer cover muss ein Bild in beiden Richtungen gross genug sein — beim
    Hineinpassen ist es das in einer Richtung nie.

    Beispiel: das Bild bei "Ueber Uns" landete bei 980x424, obwohl allein die
    Desktop-Fassung 980x794 braucht. Ergebnis: 1,87-fach hochgerechnet.

    Dazu kommt die Mobilfassung. Deren 320px-Flaeche wird vom Handy auf die
    Bildschirmbreite hochskaliert und dann mit der Pixeldichte gerendert — ein
    320px breiter Kasten braucht auf einem heutigen Telefon rund 1290 echte
    Bildpunkte, also gut das Vierfache. Nach dieser Rechnung ist bei fast allen
    Bildern ohnehin nichts zu holen.

    Die Funktion bleibt als Platzhalter stehen, damit der Grund dokumentiert
    ist und niemand es unbedacht wieder einbaut.
    """
    return None


def echtes_format(pfad):
    """Tatsaechliches Bildformat anhand der Dateisignatur.

    Wix liefert je nach Anfrage AVIF oder JPEG unter demselben Dateinamen aus.
    Traegt eine Datei .jpg, enthaelt aber AVIF, liefert der Server einen
    falschen Inhaltstyp — manche Browser zeigen das Bild dann nicht an.
    Deshalb hier gegenpruefen.
    """
    with open(pfad, "rb") as f:
        d = f.read(32)
    if d[4:12] == b"ftypavif":
        return "avif"
    if d[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if d[:3] == b"\xff\xd8\xff":
        return "jpg"
    if d[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
        return "webp"
    return None


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

        # 1. unbeschnittenes Wix-Original
        orig = os.path.join(ORIGINALS, media_id)
        if os.path.exists(orig) and os.path.getsize(orig) > 20000:
            ziel_ext = "." + media_id.rsplit(".", 1)[-1]
            target = os.path.join(DST, name + ziel_ext)
            for alt in os.listdir(DST):
                if alt.startswith(name + ".") and alt != name + ziel_ext:
                    os.remove(os.path.join(DST, alt))
            shutil.copy2(orig, target)
            manifest.append((name + ziel_ext, "Wix-Original",
                             os.path.getsize(target), purpose))
            continue

        # 2. vom Kunden geliefert
        gel = GELIEFERTE_DATEI.get(name)
        if gel:
            quelle = os.path.join(GELIEFERT, gel)
            if os.path.exists(quelle):
                ziel_ext = "." + gel.rsplit(".", 1)[-1]
                target = os.path.join(DST, name + ziel_ext)
                # alte Fassung mit anderer Endung entfernen
                for alt in os.listdir(DST):
                    if alt.startswith(name + ".") and alt != name + ziel_ext:
                        os.remove(os.path.join(DST, alt))
                shutil.copy2(quelle, target)
                manifest.append((name + ziel_ext, f"geliefert ({gel})",
                                 os.path.getsize(target), purpose))
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

    # Endung an den tatsaechlichen Inhalt anpassen
    korrigiert = []
    for i, (name, kind, size, purpose) in enumerate(manifest):
        pfad = os.path.join(DST, name)
        fmt = echtes_format(pfad)
        stamm, endung = os.path.splitext(name)
        passt = {"jpg": (".jpg", ".jpeg"), "png": (".png",), "avif": (".avif",),
                 "gif": (".gif",), "webp": (".webp",)}.get(fmt, ())
        if fmt and endung.lower() not in passt:
            neu = stamm + "." + fmt
            os.replace(pfad, os.path.join(DST, neu))
            korrigiert.append((name, neu))
            manifest[i] = (neu, kind, size, purpose)

    # Auf eine sinnvolle Groesse bringen
    verkleinert = []
    pillow_fehlt = False
    NAME_ZU_ID = {n: mid for mid, (n, _) in MAP.items()}
    for i, (name, kind, size, purpose) in enumerate(manifest):
        stamm = os.path.splitext(name)[0]
        r = verkleinern(os.path.join(DST, name), NAME_ZU_ID.get(stamm, ""))
        if r == "Pillow fehlt":
            pillow_fehlt = True
        elif r:
            vorher, nachher, groesse, noetig = r
            verkleinert.append((name, vorher, nachher, groesse, noetig))
            manifest[i] = (name, kind, nachher, purpose)

    w = max(len(m[0]) for m in manifest)
    print(f"{'Datei':<{w}}  {'Quelle':<28}  {'Groesse':>9}  Verwendung")
    print("-" * (w + 60))
    for f, kind, size, purpose in manifest:
        print(f"{f:<{w}}  {kind:<28}  {size:>8,}B  {purpose}")

    if verkleinert:
        print()
        print("Auf die noetige Groesse gebracht:")
        gespart = 0
        for name, vorher, nachher, groesse, noetig in verkleinert:
            print(f"   {name:24} {vorher/1024:7.0f} KB -> {nachher/1024:6.0f} KB  "
                  f"{groesse[0]}x{groesse[1]}  (noetig {noetig[0]}x{noetig[1]})")
            gespart += vorher - nachher
        print(f"   {'zusammen gespart':24} {gespart/1024:6.0f} KB")
    if pillow_fehlt:
        print()
        print("Hinweis: Pillow ist nicht installiert, die Bilder bleiben in")
        print("Originalgroesse. Zum Verkleinern:  pip install pillow")

    if korrigiert:
        print()
        print("Endung an den tatsaechlichen Inhalt angepasst:")
        for alt, neu in korrigiert:
            print(f"   {alt} -> {neu}")
        print("   Danach die Seiten neu erzeugen, damit die Pfade stimmen.")

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
