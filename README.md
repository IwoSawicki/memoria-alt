# memoria-alt

Statischer HTML/CSS-Nachbau von **https://www.tierbestattung-memoria.de**
(Tierbestattung Memoria, aktuell in Wix).

Zweck: Übergangslösung für ca. 2–3 Wochen, damit das Wix-Abo nicht verlängert
werden muss. Danach wird die Seite von Grund auf neu gebaut.

**Anforderung: pixelgenauer Nachbau ohne Abweichungen.**
Details siehe [`CLAUDE.md`](./CLAUDE.md).

---

## Ordnerstruktur

```
mirror/              wget-Spiegel der Originalseite (Input)
reference/screens/   Full-Page-Screenshots je Seite & Breakpoint (Input)
reference/styles/    getComputedStyle-Dumps je Seite als JSON (Input)
assets/              CSS, Bilder, Fonts, JS des Nachbaus (Output)
index.html           Startseite des Nachbaus (Output)
```

---

## 1. Mirror erstellen

```bash
mkdir -p mirror && cd mirror

wget \
  --mirror \
  --page-requisites \
  --adjust-extension \
  --convert-links \
  --no-parent \
  --span-hosts \
  --domains=www.tierbestattung-memoria.de,tierbestattung-memoria.de,static.wixstatic.com,static.parastorage.com,siteassets.parastorage.com,fonts.gstatic.com,fonts.googleapis.com \
  --execute robots=off \
  --user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" \
  --wait=1 --random-wait \
  --restrict-file-names=windows \
  --no-check-certificate \
  --tries=3 --timeout=30 \
  https://www.tierbestattung-memoria.de/
```

Anschließend die Sitemap gegenchecken, ob wget alle Unterseiten erwischt hat
(Wix verlinkt manches nur per JavaScript):

```bash
curl -s https://www.tierbestattung-memoria.de/sitemap.xml
```

Fehlende Seiten einzeln nachladen:

```bash
wget --page-requisites --adjust-extension --convert-links --span-hosts \
  --domains=www.tierbestattung-memoria.de,static.wixstatic.com,static.parastorage.com \
  --execute robots=off \
  https://www.tierbestattung-memoria.de/PFAD-DER-SEITE
```

---

## 2. Screenshots erstellen

Für **jede** Seite jeweils bei **1440px**, **768px** und **390px** Breite einen
Full-Page-Screenshot anlegen.

Chrome: DevTools öffnen → `Cmd/Ctrl + Shift + P` → „Capture full size screenshot".

Ablage: `reference/screens/<seitenname>-<breite>.png`
Beispiel: `reference/screens/startseite-1440.png`

---

## 3. Computed-Styles exportieren

Das ist der wichtigste Input für den pixelgenauen Nachbau — der Wix-HTML allein
enthält die tatsächlichen Werte nur verstreut und teilweise per JS injiziert.

Seite in Chrome öffnen, DevTools-Konsole, folgendes einfügen und ausführen.
Das Ergebnis liegt danach in der Zwischenablage:

```js
copy(JSON.stringify([...document.querySelectorAll('body *')].filter(el=>{
  const r=el.getBoundingClientRect(); return r.width>0&&r.height>0;
}).map(el=>{const c=getComputedStyle(el),r=el.getBoundingClientRect();return{
  tag:el.tagName,cls:el.className?.toString?.().slice(0,120),
  text:el.childElementCount===0?el.textContent.trim().slice(0,80):'',
  box:{x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)},
  font:[c.fontFamily,c.fontSize,c.fontWeight,c.lineHeight,c.letterSpacing,c.textTransform].join(' | '),
  color:c.color,bg:c.backgroundColor,bgImg:c.backgroundImage.slice(0,150),
  pad:c.padding,margin:c.margin,border:c.border,radius:c.borderRadius,shadow:c.boxShadow,
  display:c.display,flex:[c.flexDirection,c.justifyContent,c.alignItems,c.gap].join(' | '),
  pos:c.position,z:c.zIndex
}}),null,1))
```

Ablage: `reference/styles/<seitenname>.json`

Wichtig: Das Fenster vor dem Ausführen auf **1440px** Breite bringen, damit die
Boxmaße dem Desktop-Layout entsprechen. Optional dasselbe bei 390px als
`<seitenname>-mobile.json`.

---

## 4. Hochladen

```bash
git add mirror reference
git commit -m "Mirror und Referenzmaterial der Originalseite hinzugefügt"
git push -u origin claude/memoria-homepage-rebuild-ubm7s8
```
