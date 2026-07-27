# CLAUDE.md — Nachbau tierbestattung-memoria.de

## Projektkontext

Die bestehende Website **https://www.tierbestattung-memoria.de** (Tierbestattung Memoria)
ist in **Wix** gebaut. Das Wix-Abo soll nicht um ein weiteres Jahr verlängert werden.

Deshalb wird die Seite hier als **statische HTML/CSS-Seite 1:1 nachgebaut**. Dieser Nachbau
ist eine **Übergangslösung für ca. 2–3 Wochen**, bis die vollständig neu konzipierte Website
fertig ist und live geht.

**Daraus folgt die wichtigste Regel dieses Projekts:**
Hier wird **nichts neu gestaltet, nichts verbessert, nichts modernisiert**.
Es wird **kopiert**. So exakt wie technisch möglich.

---

## Oberstes Gebot: PIXELGENAUER NACHBAU

Der Nachbau muss vom Original **visuell nicht unterscheidbar** sein.
Wenn man Original und Nachbau als Screenshot übereinanderlegt, müssen sie deckungsgleich sein.

### Es gilt ausnahmslos:

- **Keine Abweichungen.** Nicht bei Farben, nicht bei Abständen, nicht bei Schriftgrößen.
- **Keine „Verbesserungen".** Auch wenn ein Abstand unlogisch wirkt, eine Farbe unschön ist,
  eine Schriftgröße krumm ist oder das Original einen offensichtlichen Designfehler enthält:
  **exakt so übernehmen.**
- **Keine eigenen Design-Entscheidungen.** Keine „schönere" Typo-Skala, kein aufgeräumteres
  Spacing-System, keine harmonisierten Radien, keine Design-Tokens, die Werte glattziehen.
- **Keine Modernisierung.** Kein Redesign, keine neuen Animationen, keine zusätzlichen
  Hover-Effekte, keine neuen Sections, keine umgestellte Reihenfolge.
- **Keine Vereinfachung des Layouts,** wenn sie das Ergebnis sichtbar verändert.
- **Nichts weglassen.** Jede Section, jedes Bild, jeder Button, jede Fußzeilenzeile,
  jeder Link, jeder Textabsatz wird übernommen.
- **Nichts hinzufügen.** Kein Cookie-Banner, kein Newsletter, kein „Nach oben"-Button,
  keine neuen Icons — außer es existiert im Original.

### Was exakt übereinstimmen muss

| Bereich | Anforderung |
|---|---|
| **Schriftarten** | Exakt dieselbe Font-Family. Wix nutzt oft Custom-/Google-Fonts (z.B. Madefor, Wix Madefor Display, Helvetica-Varianten). Font lokal einbinden oder via exakt derselben Quelle. Kein Ersatz durch „ähnliche" System-Fonts. |
| **Schriftgrößen** | Auf den Pixel genau (`font-size` in px, exakt wie im Original — auch 17px, 23px o.ä.). |
| **Font-Weights** | Exakt (400 ≠ 500 ≠ 600). |
| **Line-Height** | Exakt, inkl. Nachkommastellen (z.B. `1.4em`, `27px`). |
| **Letter-Spacing** | Exakt, auch `0.05em` oder negative Werte. |
| **Text-Transform** | uppercase / none exakt wie im Original. |
| **Farben** | Exakte Hex-/RGB(A)-Werte. Kein „ungefähr dasselbe Grau". Auch Transparenzen exakt. |
| **Paddings & Margins** | Pixelgenau, pro Seite und pro Element. |
| **Section-Höhen** | Exakt. Wix arbeitet häufig mit fixen Section-Höhen. |
| **Container-Breiten** | Exakte max-width des Content-Bereichs (z.B. 980px). |
| **Bilder** | Originalbilder aus dem Mirror. Exakte Anzeigegröße, `object-fit`, Bildausschnitt, Seitenverhältnis. Keine Neukomprimierung, die sichtbar wird. |
| **Border-Radius** | Exakt. |
| **Border & Shadows** | Exakt (Farbe, Breite, Offset, Blur, Spread). |
| **Buttons** | Größe, Padding, Radius, Farbe, Hover-Zustand, Schrift — exakt. |
| **Ausrichtung** | Links/zentriert/rechts exakt wie im Original. |
| **Reihenfolge** | Sections und Elemente in identischer Reihenfolge. |
| **Texte** | Wörtlich identisch, inkl. Umlauten, Groß-/Kleinschreibung, Zeilenumbrüchen, Satzzeichen und Tippfehlern. **Texte nicht umformulieren, nicht korrigieren.** |
| **Navigation** | Identische Menüpunkte, identische Beschriftung, identische Reihenfolge, identisches Verhalten. |
| **Footer** | Vollständig identisch, inkl. Kontaktdaten, Öffnungszeiten, Rechtslinks. |
| **Hover-States** | So übernehmen, wie sie im Original existieren (Farbwechsel, Unterstreichung, Opacity). |
| **Responsive** | Breakpoints und mobiles Layout wie im Original. Wix-Mobile-Ansicht separat prüfen. |

---

## Arbeitsweise

### 1. Referenzmaterial ist die Wahrheit — nicht die Erinnerung

Im Repo liegen (bzw. werden geliefert):

- `mirror/` — wget-Spiegel der Originalseite (HTML + Assets von wixstatic/parastorage)
- `reference/screens/` — Full-Page-Screenshots je Seite und Breakpoint
  (Namensschema z.B. `startseite-1440.png`, `startseite-390.png`)
- `reference/styles/` — JSON-Dumps der `getComputedStyle`-Werte je Seite

**Regel:** Bevor ein Wert (Farbe, Größe, Abstand) im Code landet, muss er aus dem
Referenzmaterial belegt sein. **Werte niemals schätzen, raten oder „nach Gefühl" setzen.**

Wenn ein Wert im Material nicht auffindbar ist:
1. Im gespiegelten HTML/CSS suchen (inline `style=`, `<style>`-Blöcke, Wix-CSS-Dateien).
2. Im Screenshot ausmessen.
3. Wenn beides scheitert: **im Code als `/* TODO: Wert unbestätigt — bitte prüfen */`
   markieren und in der Abschlussmeldung an den Nutzer auflisten.** Nicht stillschweigend
   einen Fantasiewert setzen.

### 2. Alle Unterseiten

Der Nachbau umfasst **alle Unterseiten**, nicht nur die Startseite. Vorgehen:
- Navigation und Footer des Originals auf Links prüfen
- `sitemap.xml` des Originals gegenchecken
- Jede gefundene Seite nachbauen

Für jede Seite gilt dieselbe Pixel-Genauigkeit. Auch Rechtsseiten (Impressum,
Datenschutz, AGB) werden **wörtlich** übernommen — juristische Texte niemals umschreiben,
kürzen oder „aktualisieren".

### 3. Technischer Rahmen

- **Reines HTML + CSS.** Kein Framework, kein Build-Step, kein Tailwind, kein React.
- **JavaScript nur, wo es für Funktion nötig ist** (Mobile-Menü, Slider, Akkordeon,
  Lightbox) — schlank und ohne externe Libraries, wenn möglich.
- **Keine Wix-Abhängigkeiten.** Keine Requests an `parastorage.com` / `wixstatic.com`
  zur Laufzeit. Alle Assets (Bilder, Fonts, Icons) liegen lokal im Repo.
- Semantisches, sauberes Markup — solange es das visuelle Ergebnis **nicht** verändert.
- Statisch hostbar (GitHub Pages, Netlify, beliebiger Webspace).

### 4. Struktur

```
/index.html
/<unterseite>/index.html      (oder /<unterseite>.html — einheitlich halten)
/assets/css/style.css         gemeinsame Basis
/assets/css/<seite>.css       nur falls seitenspezifisch nötig
/assets/img/
/assets/fonts/
/assets/js/
```

URL-Pfade der Originalseite beibehalten, damit bestehende Links und Suchmaschinen-
Ergebnisse weiter funktionieren.

### 5. Übernehmen, auch wenn unsichtbar

- `<title>` und `<meta name="description">` je Seite aus dem Original übernehmen
- `lang="de"`, Favicon, Open-Graph-Bilder
- `alt`-Texte der Bilder aus dem Original übernehmen

### 6. Kontrolle vor „fertig"

Vor dem Abschluss jeder Seite:
- Nachbau und Original-Screenshot nebeneinander vergleichen
- Prüfen: identische Section-Reihenfolge, identische Texte, identische Abstände
- Bei 1440px, 768px und 390px prüfen
- Abweichungen, die technisch nicht auflösbar sind, **explizit benennen** —
  nicht verschweigen und nicht schönreden

---

## Was NICHT zu tun ist

- ❌ Design „aufräumen", harmonisieren oder vereinheitlichen
- ❌ Eigene Farbpalette oder Typo-Skala einführen
- ❌ Texte umformulieren, kürzen oder Rechtschreibung korrigieren
- ❌ Sections weglassen, zusammenfassen oder umsortieren
- ❌ Neue Features, Animationen oder Elemente ergänzen
- ❌ Werte schätzen statt aus dem Referenzmaterial zu belegen
- ❌ Fehlende Bilder durch Platzhalter ersetzen, ohne es zu melden
- ❌ Abweichungen als „fertig" melden

## Der Maßstab

> Wenn der Kunde die alte und die neue Seite nebeneinander öffnet,
> soll er **keinen Unterschied** erkennen können.

Das ist das einzige Erfolgskriterium dieses Projekts.

---

## Wie am Nachbau gearbeitet wird

Der Seiteninhalt wird **nicht von Hand geschrieben, sondern erzeugt.** Grund:
Wix legt sein vollstaendiges generiertes CSS als Inline-Bloecke in jede Seite
(`css_masterPage`, `css_<seitenId>`). Dort stehen alle Masse exakt — 980px
Rasterbreite, `margin:83px 0 10px`, `min-height:445px`, Hex-Farben,
Schriftschnitte. Diese Werte werden ausgelesen statt geschaetzt.

Genauso wichtig: die Auszeichnung der Textbloecke wird **woertlich**
uebernommen. Ob ein Absatz `font_8` (15px Avenir) oder `font_7` (20px Poppins)
traegt, ob eine Leerzeile ein eigener Absatz oder ein `<br>` im selben Absatz
ist, ob eine Ueberschrift `<h1>` oder `<p>` ist — jedes dieser Details aendert
die Hoehe des Blocks und verschiebt alles darunter. Beim Abschreiben sieht man
das nicht, im Ergebnis sofort.

### Werkzeuge

```
python3 tools/original.py css|comp|dom|tree|text <seite>   Original durchsuchen
python3 tools/spec.py    <seite>                          Sollwerte auslesen
python3 tools/convert.py <seite> --write                  Seite erzeugen
python3 tools/check.py   [<seite>]                        gegen Sollwerte pruefen
node     tools/compare.js <seite> [breite]                Geometrie messen und vergleichen
python3 tools/build-images.py                             Bilder aufbereiten
```

`compare.js` braucht einmalig Playwright. Es wird nur zum Pruefen benutzt und
gehoert nicht zum ausgelieferten Stand:

```
npm install playwright        # node_modules/ ist in .gitignore
```

Die Chromium-Binary wird ueber `executablePath` in `tools/compare.js`
angesprochen. Stimmt der Pfad auf einem anderen Rechner nicht, dort anpassen
oder `npx playwright install chromium` ausfuehren.

`compare.js` ist die eigentliche Kontrolle: es rendert den wget-Mirror und den
Nachbau nebeneinander im selben Browser, misst zu jeder Komponente Position und
Groesse und meldet jede Abweichung ueber 1px. **Eine Seite gilt erst als fertig,
wenn dieser Abgleich sauber durchlaeuft.**

Nach jeder Aenderung an `tools/` alle Seiten neu erzeugen:

```
for p in index leistungen preise tierurnen-andenken pferdekremierung anfahrt kontakt; do
    python3 tools/convert.py "$p" --write
done
```

### Wenn ein Wert fehlt

Nicht schaetzen. Erst `tools/spec.py` und `tools/original.py comp` befragen. Wenn
der Wert dort nicht auftaucht, fehlt dem Extraktor eine Regel — dann den
Extraktor erweitern, nicht den Wert erfinden. Bleibt ein Wert unbelegbar: im
Code als `/* TODO: Wert unbestaetigt */` markieren und dem Nutzer melden.

---

## Bewusste Abweichungen vom Mirror

Der Mirror ist an drei Stellen **kein** getreues Abbild der Live-Seite, weil er
ohne JavaScript gerendert wird. Diese Stellen sind bewusst anders geloest und
duerfen nicht "korrigiert" werden, ohne sie vorher an der Live-Seite zu pruefen:

1. **Bestaetigungsmeldung im Kontaktformular** ("Vielen Dank fuer die
   Uebermittlung"). Im Mirror dauerhaft sichtbar, auf der Live-Seite blendet
   Wix sie per JavaScript aus. Im Nachbau versteckt, erscheint nach dem
   Absenden. Dadurch ist der Formularkasten 40px niedriger als im Mirror.

2. **Wiederholungsliste auf der Preisseite** (`comp-l56w7mxs`, enthaelt das
   Wort "Gemeinschaft"). Im Mirror auf Hoehe 0 zusammengefallen und nicht
   sichtbar. Im Nachbau ebenso. Offenbar ein liegengebliebenes leeres Element.

3. **Einblend-Animationen.** Wix startet Elemente mit Deckkraft 0 und blendet
   sie per JavaScript ein. Ohne JS bleiben sie unsichtbar. Der Nachbau zeigt
   sie direkt; `compare.js` rendert den Mirror deshalb mit `reducedMotion`.

---

## Git

- Entwicklung auf Branch `claude/memoria-homepage-rebuild-ubm7s8`
- Klare, beschreibende Commit-Messages auf Deutsch oder Englisch
- Kein Pull Request ohne ausdrückliche Aufforderung
