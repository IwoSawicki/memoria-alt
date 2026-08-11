# Nächste Schritte — Vorlage „Good Boy" für Memoria nutzen

Ziel: neue Memoria-Startseite, die sich **nah an der Good-Boy-Vorlage** hält,
aber eigene Inhalte/Anordnung hat (keine Lizenzprobleme). In diesem Ordner liegt
alles, was du dafür brauchst.

## Was schon fertig ist (von mir vorbereitet)

- **`DESIGN-SYSTEM.md`** — die komplette Gestaltung aus dem echten Quellcode
  ausgelesen: Palette (Hex), Schriften, Type-Skala, Buttons, Section-Rhythmus.
- **`PROMPT-memoria-startseite.md`** — fertiger Bauauftrag für Claude Code.
  Baut die Startseite im Good-Boy-Stil mit Memorias echten Kontaktdaten und
  Leistungen, in eigener Section-Anordnung.
- **`startseite-quelle.html`** — der Quellcode, aus dem alles ausgelesen wurde
  (zur Kontrolle).
- **`erfassen-lokal.js`** — Skript, das Screenshots und die echten Fotos zieht
  (läuft nur auf deinem Rechner, s. u.).

## Schritt 1 — Palette-Entscheidung (2 Minuten)

Die eine Design-Entscheidung, die du treffen solltest: Die Vorlage nutzt als
Akzent eine **helle Limette** (`#C4D35B`) — passend für Hundetraining, aber für
ein Tierkrematorium zu fröhlich. Mein Vorschlag im Prompt: gedecktes **Oliv**
(`#6C7E4E`). Alternativ deine Memoria-Markenfarbe. Sag mir, was du willst, oder
lass es beim Oliv.

## Schritt 2 — Referenzbilder ziehen (auf deinem Rechner)

Ich komme aus dieser Umgebung nicht ins offene Internet (Netzsperre), du schon.
So holst du Screenshots **und** die echten Fotos der Vorlage:

```bash
mkdir memoria-referenz && cd memoria-referenz
npm init -y && npm install playwright && npx playwright install chromium
# erfassen-lokal.js aus reference/goodboy/ hierher kopieren
node erfassen-lokal.js
```

Danach liegen in `reference/goodboy/`: `desktop-1440.png`, `mobil-390.png`,
`init_data.json` und ein Ordner `bilder/` mit allen Fotos. Die Screenshots sind
die Vorlage fürs Auge, an der Claude Code sich orientiert.

> Falls du kein Node/Playwright einrichten willst: es reicht auch, die Seite im
> Browser zu öffnen und mit einer „Full Page Screenshot"-Funktion (Firefox:
> Rechtsklick → „Screenshot erstellen" → „Ganze Seite") bei 1440px und 390px
> Breite je ein Bild zu speichern. Die Fotos der Vorlage brauchst du aber
> ohnehin **nicht** — Memoria bekommt eigene Bilder.

## Schritt 3 — Memoria-Fotos bereitstellen

Eigene Bilder sind der wichtigste Hebel gegen Lizenzärger. Du hast bereits die
Memoria-Fotos (im Wix-Projekt unter `bilder-memoria/`). Leg passende davon in
`assets/img/` des neuen Projekts: 1 ruhiges Hero-Foto (Natur/Tier/Kerze), 1
Porträt/Innenraum fürs „Über uns", 3 Leistungsbilder, 1 Andenken-/Urnen-Foto,
1 Abschluss-Foto. Wo etwas fehlt, markiert Claude Code es als Platzhalter.

## Schritt 4 — Startseite bauen lassen

Neues, leeres Projektverzeichnis, Claude Code starten, den Inhalt von
`PROMPT-memoria-startseite.md` hineinkopieren. Screenshots und Fotos vorher
hineinlegen (Schritt 2 + 3). Ergebnis: eine responsive Memoria-Startseite im
Good-Boy-Stil, reines HTML/CSS.

## Schritt 5 — Feinschliff & Unterseiten

Wenn die Startseite sitzt, dieselbe Design-Sprache auf die Unterseiten
(Leistungen, Preise, Tierurnen & Andenken, Pferdekremierung, Kontakt) ausrollen.
Dafür sage ich dir gern die passenden Folge-Prompts — dann bleibt alles
konsistent.

---

### Kurzfassung „was mache ich als Nächstes"
1. Palette bestätigen (Oliv oder Memoria-Farbe).
2. `erfassen-lokal.js` lokal laufen lassen → Screenshots.
3. Memoria-Fotos in `assets/img/` legen.
4. `PROMPT-memoria-startseite.md` in Claude Code einfügen → Startseite entsteht.
5. Danach Unterseiten (Prompts bekommst du von mir).
