# Design-System der Vorlage „Good Boy" (Showit)

Quelle: `goodboy.riverwoodcreative.com` — verkaufte Showit-Vorlage von Riverwood
Creative. **Alle Werte unten sind aus dem echten Quellcode (`init_data`,
Inline-CSS) ausgelesen, nichts geschätzt.** Diese Datei ist die Grundlage, um
den *Stil* auf Memoria zu übertragen — nicht die Vorlage selbst zu kopieren.

> **Lizenz:** Die Vorlage wird verkauft (`riverwoodcreative.com/goodboy`). Als
> Stil-Vorbild (Palette, Schrift-Paarung, Rhythmus) unproblematisch. Eine
> pixelidentische Kopie mit denselben Bildern/Texten wäre es nicht. Deshalb:
> eigene Inhalte, eigene Bilder, eigene Section-Anordnung. Siehe Bauauftrag.

---

## Technischer Rahmen (wie es gebaut ist)

| | Wert |
|---|---|
| Plattform | Showit (Engine `lib.showit.co/engine/2.8.0`) |
| Layout | feste Leinwand, jedes Element absolut positioniert |
| Desktop-Breite | **1200px** |
| Mobil-Breite | **320px** |
| Breakpoint | **768px** (`.d` = Desktop, `.m` = Mobil) |
| Sections | 16 Blöcke, davon 3 reine Vorlagen-Hinweise (löschbar) |

Für einen echten Nachbau gilt dasselbe wie bei Wix: nicht responsiv, zwei feste
Fassungen. Für ein **neues** Memoria-Design bauen wir das **nicht** nach — wir
übernehmen nur die Gestaltung und bauen sie modern & responsiv (Flexbox/Grid).

---

## Farbpalette

| Rolle | RGBA | Hex | Einsatz |
|---|---|---|---|
| Dunkelgrün (Grundton) | `rgba(15,29,2,1)` | `#0F1D02` | Text, dunkle Sections, Footer |
| Fast-Schwarz-Grün | `rgba(15,24,12,1)` | `#0F180C` | tiefe Flächen, Overlays |
| Limette (Akzent) | `rgba(196,211,91,1)` | `#C4D35B` | Buttons, Highlights, Linien |
| Oliv | `rgba(108,126,78,1)` | `#6C7E4E` | Sekundärtext, Icons |
| Creme (hell) | `rgba(246,250,235,1)` | `#F6FAEB` | helle Sections, Grundfläche |
| Blassgrün | `rgba(233,239,215,1)` | `#E9EFD7` | zweite helle Fläche |
| Weiß | `rgba(255,255,255,1)` | `#FFFFFF` | Text auf dunkel, Karten |

Transparenzen im Einsatz: `rgba(15,29,2,0.4 / 0.75 / 0.9)` (Overlays auf
Hero-Bildern), `rgba(246,250,235,0.5)` (gedämpfter heller Text).

> **Ton-Hinweis für Memoria:** Die Palette ist ruhig und naturnah — passt
> erstaunlich gut zu „Erinnerung / Frieden / Natur". Nur die **helle Limette
> `#C4D35B`** wirkt fröhlich-sportlich (Hundetraining). Für einen Trauer-/
> Gedenk-Kontext würde ich sie zu einem gedeckteren Grün-/Salbeiton oder zu
> Memorias vorhandener Markenfarbe verschieben. Das ist die **eine** bewusste
> Design-Entscheidung, die du treffen solltest — Rest bleibt.

---

## Typografie

Zwei Schriften, beide Google Fonts:

**Libertinus Sans** — Überschriften. Nur Regular (400). Eine ruhige,
humanistische Serifenlose mit leicht literarischem Charakter.

**Figtree** — Fließtext, Navigation, Buttons, Labels. Weights 400 / 600 / 700.

### Type-Skala (Desktop, ausgelesen)

| Rolle | Font | Größe | Line-height | Besonderheit |
|---|---|---|---|---|
| Hero-Headline | Libertinus Sans 400 | **76px** | 1.0 | |
| Section-Headline | Libertinus Sans 400 | **48px** | 1.05 | |
| Sub-Headline | Libertinus Sans 400 | **36px** | 1.0 | |
| Fließtext | Figtree 400 | **16px** | ~1.5 | |
| Klein / Karten | Figtree 400/600 | 14–15px | | |
| Label / Kicker | Figtree 600 | **12px** | | `uppercase`, `letter-spacing:0.3em` |
| Oversize-Display | (dekorativ) | 80–120px | 0.9–1.0 | große Akzent-Wörter/Zahlen |

Laufweite: Standard `letter-spacing:0.02em`; Kicker-Labels `0.3em`;
Überschriften teils leicht negativ (`-0.02em`).

### Mobil
Hero-Headline fällt auf ~46–48px, Section-Headlines entsprechend kleiner.
Grundprinzip: gleiche Schriften, ~40 % kleinere Display-Größen.

---

## Buttons & Formen

- **Primär-Button:** Pille, `border-radius:60px`, Figtree, Label oft `uppercase`.
  Limette-Fläche auf Dunkelgrün bzw. Dunkelgrün auf Hell.
- Sekundäre Radien im Einsatz: 14px, 20px, 30px (Karten/Bilder).
- Icons: eigene Icon-Sprites (Pfoten, Häkchen). Im Nachbau durch eigene
  schlichte Line-Icons ersetzen.

---

## Section-Rhythmus (das Herz der Vorlage)

Reihenfolge der sichtbaren Startseite (Vorlagen-Hinweis-Blöcke entfernt), mit
Hintergrundfarbe. Der Reiz entsteht durch den **Wechsel dunkel ↔ hell** und
gestapelte Service-Karten mit 20px-Versatz.

| # | Block | Hintergrund | Inhalt |
|---|---|---|---|
| 1 | Navigation | transparent über Hero | Logo, Menü, ein CTA |
| 2 | **Hero** | Bild + Dunkelgrün-Overlay | große Headline, Subline, CTA, 3 Trust-Punkte |
| 3 | Unser Ansatz | Creme `#F6FAEB` | 3 Wert-Säulen mit Icon + Text |
| 4 | Über uns | Creme `#F6FAEB` | Portrait + Vorstellung + CTA |
| 5 | Leistung 1 | Blassgrün `#E9EFD7` | Karte: Bild + Titel + Text + Button |
| 6 | Leistung 2 | (gestapelt, 20px Versatz) | Karte |
| 7 | Leistung 3 | (gestapelt, 20px Versatz) | Karte |
| 8 | Stimmen | Dunkelgrün `#0F1D02` | Kundenzitate, heller Text |
| 9 | Freebie/Ratgeber | Bild + Overlay | Lead-Magnet, E-Mail-Opt-in |
| 10 | Aktuelles/Blog | Blassgrün `#E9EFD7` | 3 Beitragskarten |
| 11 | Abschluss-CTA | Bild + Dunkel-Overlay | eine große Schluss-Aufforderung |
| 12 | Footer | Dunkelgrün `#0F1D02` | Navigation, Claim, Kontakt, Recht |

**Gestaltungsmerkmale, die den Look ausmachen:**
- viel Weißraum, große ruhige Headlines in Libertinus Sans
- kleine `uppercase`-Kicker-Labels über jeder Headline
- warmer, natürlicher Grün-/Creme-Wechsel statt hartem Schwarz/Weiß
- Pillen-Buttons, weiche Bildradien
- Hero und CTA jeweils Foto mit dunklem Grün-Overlay + hellem Text
