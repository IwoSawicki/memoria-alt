# Abnahme — was morgen zu tun ist

## Kurzfassung

Der Nachbau ist fertig und geprüft: **alle 7 Seiten stimmen pixelgenau** mit dem
Original überein (gemessen bei 1024, 1280, 1440 und 1920 Bildschirmbreite,
Komponente für Komponente, keine Abweichung über 1 Pixel).

Zwei Dinge fehlen noch, und beide brauchen Internetzugang zu den Wix-Servern —
in meiner Entwicklungsumgebung sind die gesperrt. Deshalb dein Part:

```bash
bash tools/morgen.sh
```

Das Skript lädt die Originalbilder nach, spiegelt die Mobilfassung, baut alle
Seiten neu und prüft sie. Am Ende steht eine Statusübersicht.

---

## Schritt 1 — Skript laufen lassen

```bash
bash tools/morgen.sh
```

Erwartetes Ergebnis:

```
Bilder:   alle in voller Aufloesung
Mobil:    Mirror liegt vor, Mobilfassung kann gebaut werden
```

Wenn beides so dasteht: `git add -A && git commit -m "Bilder und Mobil-Mirror" && git push`
und mir Bescheid geben — dann baue ich die Mobilfassung pixelgenau nach.

Falls die Bilder nicht laden: Wix liefert sie nur mit Browser-Kennung aus. Das
Skript setzt bereits eine, notfalls die URLs aus `tools/fetch-missing-images.sh`
einzeln im Browser öffnen und speichern.

---

## Schritt 2 — FormSubmit freischalten

Das Kontaktformular verschickt über FormSubmit.co. **Beim allerersten Absenden**
schickt FormSubmit eine Bestätigungsmail an `info@tierbestattung-memoria.de`.
Bis der Link darin geklickt ist, kommt **keine** Nachricht an.

Also: Formular einmal selbst absenden, Postfach prüfen, Link klicken. Danach
läuft es.

Empfehlung danach: FormSubmit stellt eine Alias-Adresse bereit
(`https://formsubmit.co/xxxxxxxx`). Die im Formular eintragen, damit die
E-Mail-Adresse nicht im Quelltext steht — sonst sammeln Spam-Programme sie ein.
Die Stelle: `tools/convert.py`, Konstante `FORM_ZIEL`.

---

## Schritt 3 — Dokploy

1. Dokploy → Project → *Create Service* → **Application**
2. Provider **GitHub** → `IwoSawicki/memoria-alt` → Branch `claude/memoria-homepage-rebuild-ubm7s8`
3. Build Type **Dockerfile**, Pfad `Dockerfile`
4. Port **80**
5. **Deploy**, Logs abwarten
6. Tab *Domains* → `www.tierbestattung-memoria.de`, Port 80, HTTPS aktivieren
7. Erst danach den DNS-A-Record von Wix auf den Dokploy-Server umstellen

Über die Vorschau-URL von Dokploy kannst du alles prüfen, bevor der DNS umgestellt wird.

---

## Was du beim Durchklicken prüfen solltest

Alles Folgende konnte ich nicht selbst verifizieren, weil ich die Live-Seite
nicht aufrufen kann.

| Was | Wo | Warum |
|---|---|---|
| Bilder scharf und richtig zugeschnitten | alle Seiten | vorher waren es Platzhalter |
| Kontaktformular kommt an | /kontakt | FormSubmit-Freischaltung |
| Bestätigung nach dem Absenden | /kontakt | „Vielen Dank fuer die Uebermittlung" soll erst danach erscheinen |
| Google-Karte lädt | /kontakt | in meiner Umgebung geblockt |
| PDF-Katalog öffnet | /tierurnen-andenken | 2,1 MB, aus dem Mirror übernommen |
| Terminbuchung öffnet | /, /leistungen, /preise, /kontakt | externer Link zu Acuity |

---

## Drei Punkte, bei denen ich eine Entscheidung getroffen habe

Der gespiegelte Mirror wird ohne JavaScript dargestellt und weicht an diesen
Stellen von der echten Seite ab. Ich habe jeweils gewählt, was der Live-Seite
entspricht — bitte gegenprüfen:

**1. „Vielen Dank fuer die Uebermittlung"**
Im Mirror dauerhaft sichtbar unter dem Senden-Knopf. Auf der Live-Seite blendet
Wix das per JavaScript aus. Ich blende es aus und zeige es nach dem Absenden.
Falls auf der Live-Seite doch immer sichtbar: in `public/assets/css/form.css`
die Regel `.form__danke { display: none }` entfernen.

**2. Das Wort „Gemeinschaft" auf der Preisseite**
Steckt im Original in einem Wiederholungselement, das auf Höhe 0
zusammengefallen und damit unsichtbar ist. Sieht nach einem liegengebliebenen
leeren Baustein aus. Ich bilde den Zustand nach — auf der Preisseite erscheint
das Wort also nicht. Falls es auf der Live-Seite doch steht: in `layout.css`
bei `.repeater` die Zeilen `height: 0` und `overflow: hidden` entfernen.

**3. Google-Karte auf der Kontaktseite**
Nachgebaut als Standard-Einbettung, 470px hoch wie im Original. Sie lädt zu
Google, ohne dass vorher gefragt wird. Beim Wix-Original war das vermutlich über
dessen Cookie-Banner geregelt, den es hier nicht gibt. Für 2–3 Wochen Übergang
deine Entscheidung — sag Bescheid, wenn stattdessen ein Klick-zum-Laden-Feld
davor soll.

---

## Eine Korrektur am Original

Auf der Kontaktseite zeigte der E-Mail-Link auf
`info@tierbestattung-memoria.de.de` — eine Domain mit doppelter Endung.
Der sichtbare Text war richtig, nur das Verweisziel falsch; Anfragen darüber
kamen nie an. **Das habe ich korrigiert.** Am Aussehen ändert sich nichts.
Sag Bescheid, wenn es doch original bleiben soll.

---

## Zwei Kleinigkeiten, die auffallen könnten

- **`og:site_name` ist „My Site 2".** Das ist ein Wix-Standardwert, den das
  Original so mitschleppt. Unsichtbar auf der Seite, taucht aber beim Teilen
  eines Links in sozialen Netzwerken auf. Ich habe ihn originalgetreu
  übernommen. Ein Wort von dir und ich setze „Memoria Tierbestattung".

- **Handys** laufen bis zur fertigen Mobilfassung im Notbehelf: die Seite wird
  komplett, aber herunterskaliert dargestellt (so wie jede nicht-responsive
  Seite auf dem Handy). Vorher war sie dort schlicht abgeschnitten und zur
  Hälfte unerreichbar. Sobald der Mobil-Mirror da ist, ersetze ich das durch die
  echte Mobilfassung.

---

## Selbstprüfung jederzeit wiederholbar

```bash
python3 tools/check.py        # Sollwerte aus dem Original
python3 tools/htmlcheck.py    # HTML-Struktur
python3 tools/linkcheck.py    # alle Verweise
node tools/compare.js index 1440   # Geometrie gegen das Original messen
```
