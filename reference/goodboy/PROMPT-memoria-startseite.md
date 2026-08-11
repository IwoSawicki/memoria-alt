# Bauauftrag für Claude Code — Memoria-Startseite im „Good Boy"-Stil

> So benutzt du diese Datei: neues, leeres Projektverzeichnis anlegen, Claude
> Code darin starten, den gesamten Block unterhalb der Linie hineinkopieren.
> Lege vorher die Referenzbilder daneben (siehe `NEXT-STEPS.md`, Schritt 2):
> `reference/screens/goodboy-desktop-1440.png` und `-mobil-390.png`, außerdem
> die Memoria-Fotos in `assets/img/`.

---

Du baust die **Startseite einer neuen Website** für **Memoria Tierbestattung
GmbH** (Tierkrematorium, Laudenbach, Region Rhein-Main-Neckar). Es geht in
diesem Schritt **nur um das Design** — kein Backend, kein CMS, keine
Formular-Anbindung, keine Framework-Diskussion. Reines, sauberes,
**responsives** HTML + CSS (Flexbox/Grid). Wenig, schlankes JS nur für
Mobil-Menü.

## Gestaltungsvorbild

Als Gestaltungsvorbild dient die Referenz in `reference/screens/goodboy-*.png`
(eine ruhige, naturnahe Design-Sprache mit Grün-/Creme-Palette, großen
Serifenlos-Headlines und viel Weißraum). **Übernimm die Design-Sprache, nicht
die Seite Eins-zu-eins** — es ist eine fremde, verkaufte Vorlage. Konkret heißt
das: gleiche Stimmung, gleiche Palette, gleiche Schrift-Paarung, gleicher
Rhythmus aus dunklen und hellen Sections — aber **eigene Section-Anordnung,
eigene Bilder, eigene Texte** (unten geliefert).

## Design-Tokens (verbindlich)

**Farben**
```
--gruen-dunkel:  #0F1D02;   /* Grundton, Text, dunkle Sections, Footer */
--gruen-tief:    #0F180C;   /* Overlays auf Fotos */
--akzent:        #6C7E4E;   /* Akzent/Buttons — gedecktes Oliv, siehe Hinweis */
--olive:         #6C7E4E;   /* Sekundärtext, Icons */
--creme:         #F6FAEB;   /* helle Grundfläche */
--blassgruen:    #E9EFD7;   /* zweite helle Fläche */
--weiss:         #FFFFFF;
```
> Hinweis: Das Vorbild nutzt als Akzent eine helle Limette `#C4D35B`. Für ein
> Tierkrematorium (Trauer/Gedenken) ist das zu fröhlich. Setze den Akzent
> deshalb auf das gedecktere Oliv `#6C7E4E`. Wenn eine Memoria-Markenfarbe
> geliefert wird, ersetze `--akzent` dadurch — an **einer** Stelle.

**Schrift** (Google Fonts, lokal einbinden oder via Google laden)
- Überschriften: **Libertinus Sans**, weight 400
- Text/UI/Buttons: **Figtree**, weights 400 / 600 / 700

**Type-Skala** (Desktop → skaliert responsiv nach unten)
```
Hero-Headline     Libertinus Sans 400   76px / lh 1.0   (mobil ~44px)
Section-Headline  Libertinus Sans 400   48px / lh 1.05  (mobil ~34px)
Sub-Headline      Libertinus Sans 400   36px / lh 1.0
Fließtext         Figtree 400           16px / lh 1.5
Kicker-Label      Figtree 600           12px, uppercase, letter-spacing .3em
```

**Formen**
- Primär-Buttons: Pille, `border-radius: 60px`, Label groß & ruhig
- Bild-/Karten-Radius: 14–20px
- Icons: schlichte Line-Icons (Pfote, Häkchen, Blatt) — dezent

**Raster**
- Content-Breite max. **1200px**, zentriert, großzügige Außenabstände
- vollflächige Section-Hintergründe, Inhalt im 1200er-Container
- **responsiv** (nicht wie das Vorbild feste Leinwand): 1 Spalte auf Mobil,
  2–3 Spalten ab 768px

## Section-Aufbau der Startseite (eigene Reihenfolge)

Wechsel dunkel ↔ hell einhalten. Jede Section bekommt einen kleinen
uppercase-Kicker über der Headline.

1. **Kopf/Navigation** — Logo links, Menü: *Startseite · Leistungen · Preise ·
   Tierurnen & Andenken · Pferdekremierung · Kontakt*; rechts ein Button
   „Termin buchen".
2. **Hero** (Foto + Dunkelgrün-Overlay, heller Text): Kicker „TIERKREMATORIUM ·
   RHEIN-MAIN-NECKAR", Headline z. B. *„Ein würdevoller Abschied für Ihren
   treuen Begleiter"*, kurze Subline, Primär-Button „Beratung anfragen",
   darunter 3 Trust-Punkte (z. B. *Einzelkremierung mit Rückgabe der Asche · 
   Persönliche Betreuung · Eigenes Krematorium*).
3. **Werte / Unser Versprechen** (Creme): 3 Säulen mit Icon —
   *Würde · Nähe · Transparenz*, je 1 Satz.
4. **Über Memoria** (Creme): Foto + Text über das Haus/Team; Claim aus dem
   Original ruhig aufgreifen: *„Auf uns ist Verlass. Darauf geben wir unser
   Wort."* Button „Mehr über uns".
5. **Leistungen** (Blassgrün, 3 gestapelte Karten mit ~20px Versatz):
   *Einzelkremierung · Sammelkremierung · Pferdekremierung* — je Bild, Titel,
   1–2 Sätze, Button „Mehr erfahren".
6. **Stimmen** (Dunkelgrün, heller Text): 2–3 kurze Kundenzitate von
   Tierhaltern (Platzhalter, klar als solche markiert).
7. **Tierurnen & Andenken** (Foto + Overlay): Hinweis auf das Sortiment,
   Button „Zum Katalog".
8. **Abschluss-CTA** (Foto + Dunkel-Overlay): eine große Aufforderung —
   *„Wir sind rund um die Uhr für Sie da."* + Button „Kontakt aufnehmen".
9. **Footer** (Dunkelgrün): Kontaktdaten (unten), Menü, Rechtslinks.

## Echte Inhalte (Fakten — wörtlich verwenden)

```
Firma:        Memoria Tierbestattung GmbH
Sitz:         Konrad-Zuse-Str. 3, 69514 Laudenbach
Abholadresse: Carl-Benz-Str. 1, 64683 Einhausen
Telefon:      0 62 01 - 7 30 30 41
E-Mail:       info@tierbestattung-memoria.de
Rechtslinks:  Impressum · Impressum/AGB · Datenschutzerklärung
Terminbuchung: „Link zum Online-Terminbuchung" (Button, Ziel später)
```
Menü und Leistungsnamen exakt: *Home/Startseite, Leistungen, Preise, Tierurnen
& Andenken, Pferdekremierung, Kontakt*.

Marketing-Texte, die du nicht faktisch belegen kannst (Hero-Subline, Zitate,
Wert-Beschreibungen), formulierst du **warm, schlicht, würdevoll** und
markierst sie im Code mit `<!-- PLATZHALTER: bitte final abstimmen -->`, damit
der Kunde sie freigibt. Keine erfundenen Fakten (Preise, Zahlen, Namen).

## Technische Vorgaben

- Struktur: `index.html`, `assets/css/style.css`, `assets/js/menu.js`,
  `assets/fonts/`, `assets/img/`.
- `lang="de"`, sinnvolle `<title>`/`<meta description>`, `alt`-Texte.
- Mobil-Menü als Overlay (Hamburger), sonst kein JS.
- Sauberes, semantisches Markup; CSS mit den Tokens oben als
  `:root`-Custom-Properties.
- Keine externen Abhängigkeiten außer den zwei Google Fonts.
- Am Ende: kurze Notiz, welche Bilder/Texte noch fehlen.
