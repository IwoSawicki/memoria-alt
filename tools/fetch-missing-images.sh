#!/usr/bin/env bash
# Lädt die Original-Bilddateien von Wix nach.
#
# Hintergrund: Wix lazy-loaded Bilder. Der wget-Mirror hat bei 7 der 13 Bilder
# nur den winzigen, unscharfen Platzhalter (LQIP, z.B. 61x41px mit blur_2)
# erwischt — nicht das echte Bild. Ohne diese Datei-Downloads sind die Bilder
# im Nachbau unbrauchbar.
#
# Dieses Skript holt die Originale in voller Auflösung (ohne Wix-Transformation).
# Der Zuschnitt wird im Nachbau per CSS (object-fit: cover, zentriert)
# reproduziert — das entspricht exakt Wix' "al_c"-Crop.
#
# Ausführen im Repo-Root:   bash tools/fetch-missing-images.sh
# Danach:                   git add originals && git commit && git push

set -euo pipefail

OUT="originals"
mkdir -p "$OUT"

IDS=(
  "11062b_0ff25f13cb54428289ab2905e75f59ea~mv2.jpg"    # Startseite, Hero 980x445
  "11062b_16e659636eb643b095afb55c48f8f449~mv2.jpg"    # Leistungen, 245x436
  "11062b_4d60829cc0024ce3b99663000f52efdb~mv2.jpeg"   # Startseite, 490x397
  "11062b_55e976feb9ef42ae87ff8eef2269e582~mv2.jpg"    # Leistungen, 245x436
  "11062b_880c7b78f2784cb48e182e145a301663~mv2.jpeg"   # 5 Seiten, 619x362
  "2ef2dc_7ceb7be074d543a194047a68ccc64c4a~mv2.jpg"    # Startseite, 490x709
  "9d970e_942cbe5236fb4b8fbe3665173da84739~mv2.png"    # alle Seiten, 287x132
  # Die folgenden liegen bereits in brauchbarer Auflösung vor, werden aber
  # zur Sicherheit als Original mitgeholt (verlustfrei, kein AVIF-Recompress):
  "11062b_3b0b289dbe5448a088a870b81290b4fc~mv2.jpg"    # Kontakt, "Dog Friends"
  "9d970e_23caadb871044f1e9c0f72221f3efea6~mv2.png"    # Favicon
  "9d970e_4171dcf38b454e389f119377c2543260~mv2.jpg"    # Pferdekremierung
  "9d970e_54937a25a3f54639a74669d6e73cf288~mv2.png"    # alle Seiten
  "9d970e_ccc93739c7b14e5f9f41a9bca3fa8d51~mv2.png"    # Logo hell
  "9d970e_eab4cd8ba69d4859919ff5192b7dffc7~mv2.jpg"    # Tierurnen
)

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

for id in "${IDS[@]}"; do
  echo "-> $id"
  wget --quiet --show-progress \
       --user-agent="$UA" \
       --tries=3 --timeout=30 \
       -O "$OUT/$id" \
       "https://static.wixstatic.com/media/$id"
done

echo
echo "Fertig. Ergebnis:"
ls -lh "$OUT"
echo
echo "Plausibilitaetscheck: jede Datei sollte deutlich groesser als 10 KB sein."
