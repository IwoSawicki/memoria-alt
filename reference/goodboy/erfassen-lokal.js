// Erfasst die Showit-Vorlage als Referenz — AUF DEINEM RECHNER auszuführen,
// weil die Cloud-Umgebung nicht ins offene Internet darf.
//
// Ergebnis in reference/goodboy/:
//   desktop-1440.png, mobil-390.png   Full-Page-Screenshots
//   startseite.html                   gerendertes HTML
//   init_data.json                    alle Layout-Koordinaten
//   bilder/                           alle nachgeladenen Fotos (echte Dateien)
//   bild-urls.txt                     Liste der Bild-URLs
//
// Einmalig vorbereiten:
//   npm init -y
//   npm install playwright
//   npx playwright install chromium
// Dann:
//   node erfassen-lokal.js

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const https = require('https');

const URL = 'https://goodboy.riverwoodcreative.com/';
const OUT = path.join(process.cwd(), 'reference', 'goodboy');
const IMG = path.join(OUT, 'bilder');

const BREITEN = [
  { name: 'desktop-1440', width: 1440, height: 1000 },
  { name: 'mobil-390',    width: 390,  height: 844 },
];

function laden(url, ziel) {
  return new Promise((res) => {
    const u = url.startsWith('//') ? 'https:' + url : url;
    const f = fs.createWriteStream(ziel);
    https.get(u, (r) => { r.pipe(f); f.on('finish', () => f.close(res)); })
         .on('error', () => res());
  });
}

async function ganzScrollen(page) {
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      let y = 0; const s = 400;
      const t = setInterval(() => {
        window.scrollTo(0, y); y += s;
        if (y >= document.body.scrollHeight) {
          clearInterval(t); window.scrollTo(0, 0); resolve();
        }
      }, 120);
    });
  });
  await page.waitForTimeout(2500);
}

(async () => {
  fs.mkdirSync(IMG, { recursive: true });
  const browser = await chromium.launch();
  const bildUrls = new Set();

  for (const b of BREITEN) {
    const ctx = await browser.newContext({
      viewport: { width: b.width, height: b.height },
      deviceScaleFactor: 2,
    });
    const page = await ctx.newPage();
    page.on('response', (r) => {
      const u = r.url();
      if (u.includes('static.showit.co')) bildUrls.add(u);
    });

    console.log('Lade', b.name, '...');
    await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
    await ganzScrollen(page);
    await page.screenshot({ path: path.join(OUT, b.name + '.png'), fullPage: true });
    console.log('  ->', b.name + '.png');

    if (b.name.startsWith('desktop')) {
      const init = await page.evaluate(() => {
        const el = document.getElementById('init_data');
        return el ? el.textContent : null;
      });
      if (init) fs.writeFileSync(path.join(OUT, 'init_data.json'), init);
      fs.writeFileSync(path.join(OUT, 'startseite.html'), await page.content());
    }
    await ctx.close();
  }

  console.log('\nLade', bildUrls.size, 'Bilder ...');
  let i = 0;
  for (const u of [...bildUrls].sort()) {
    const name = String(i).padStart(3, '0') + '-' + (u.split('/').pop().split('?')[0] || 'bild');
    await laden(u, path.join(IMG, name));
    i++;
  }
  fs.writeFileSync(path.join(OUT, 'bild-urls.txt'), [...bildUrls].sort().join('\n') + '\n');
  console.log('Fertig. Screenshots + Bilder liegen in reference/goodboy/');

  await browser.close();
})();
