/*
 * Geometrie-Abgleich zwischen Original und Nachbau.
 *
 * Der wget-Mirror enthaelt das vollstaendige generierte Wix-CSS und den
 * serverseitig gerenderten DOM. Damit laesst sich die Originalseite lokal
 * rendern und als Messreferenz benutzen — ohne die Seite aufzurufen.
 *
 * Das Skript oeffnet beide Seiten in derselben Fenstergroesse, misst zu jeder
 * Komponente die Position und Groesse und meldet jede Abweichung ueber der
 * Toleranz.
 *
 * Zuordnung: im Original ueber die Wix-Kennung (#comp-xxxx), im Nachbau ueber
 * das Attribut data-comp="comp-xxxx".
 *
 * Zwei Eigenheiten des Mirrors werden ausgeglichen:
 *  - Wix blendet Elemente per JavaScript ein. Ohne JS bleiben sie auf
 *    Deckkraft 0 stehen, deshalb laeuft das Rendern mit reducedMotion.
 *  - Der Menuepunkt "More" wird normalerweise per JavaScript ausgeblendet.
 *
 * Aufruf:  node tools/compare.js <seite> [breite]
 *          node tools/compare.js index 1440
 */
const { chromium } = require('playwright');
const path = require('path');

const EXE = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const ROOT = path.resolve(__dirname, '..');
const TOLERANZ = 1; // Pixel

async function messen(browser, url, selektorBauer, breite, istOriginal) {
  const ctx = await browser.newContext({
    viewport: { width: breite, height: 1000 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
    javaScriptEnabled: !istOriginal,
  });
  const page = await ctx.newPage();
  await page.goto(url, { waitUntil: 'load' }).catch(() => {});
  await page.waitForTimeout(1200);

  if (istOriginal) {
    // "More" wird im echten Betrieb per JavaScript ausgeblendet.
    // Nicht ueber addStyleTag einfuegen: das wartet auf ein Load-Ereignis,
    // das bei abgeschaltetem JavaScript nie eintrifft.
    await page.evaluate(() => {
      const s = document.createElement('style');
      s.textContent = '[id$="__more__"] { display: none !important; }';
      document.head.appendChild(s);
    });
    await page.waitForTimeout(200);
  }

  const daten = await page.evaluate((istOrig) => {
    const raus = {};
    const knoten = istOrig
      ? document.querySelectorAll('[id^="comp-"]')
      : document.querySelectorAll('[data-comp]');
    knoten.forEach((el) => {
      const id = istOrig ? el.id : el.getAttribute('data-comp');
      if (raus[id]) return;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) return;
      raus[id] = {
        x: Math.round(r.x),
        y: Math.round(r.y + window.scrollY),
        w: Math.round(r.width),
        h: Math.round(r.height),
      };
    });
    return { boxen: raus, hoehe: document.documentElement.scrollHeight };
  }, istOriginal);

  await ctx.close();
  return daten;
}

(async () => {
  const seite = process.argv[2] || 'index';
  const mobil = process.argv.includes('--mobile');
  // Die Mobilfassung des Originals ist auf 320px ausgelegt.
  const breite = parseInt(process.argv[3] && /^\d+$/.test(process.argv[3])
    ? process.argv[3] : (mobil ? '320' : '1440'), 10);

  const spiegel = mobil ? 'miror-mobile' : 'miror-alt';
  const nachbau = mobil ? path.join('public', 'm') : 'public';
  const urlOriginal = 'file://' + path.join(ROOT, spiegel, 'www.tierbestattung-memoria.de', seite + '.html');
  const urlNachbau = 'file://' + path.join(ROOT, nachbau, seite + '.html');

  const browser = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox'] });
  const orig = await messen(browser, urlOriginal, null, breite, true);
  const neu = await messen(browser, urlNachbau, null, breite, false);
  await browser.close();

  console.log(`Seite: ${seite}   Breite: ${breite}px${mobil ? '   (Mobilfassung)' : ''}`);
  console.log(`Gesamthoehe   Original ${orig.hoehe}px   Nachbau ${neu.hoehe}px   ` +
              `Differenz ${neu.hoehe - orig.hoehe}px`);
  console.log('');

  const ids = Object.keys(neu.boxen).sort();
  if (!ids.length) {
    console.log('Keine data-comp-Elemente im Nachbau gefunden.');
    return;
  }

  const abweichungen = [];
  let geprueft = 0;

  for (const id of ids) {
    const o = orig.boxen[id];
    const n = neu.boxen[id];
    if (!o) {
      abweichungen.push(`  ${id}: im Original nicht messbar`);
      continue;
    }
    geprueft++;
    const d = { x: n.x - o.x, y: n.y - o.y, w: n.w - o.w, h: n.h - o.h };
    const schlimm = Object.entries(d).filter(([, v]) => Math.abs(v) > TOLERANZ);
    if (schlimm.length) {
      abweichungen.push(
        `  ${id.padEnd(22)} ` +
        schlimm.map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`).join('  ') +
        `   (Original ${o.x},${o.y} ${o.w}x${o.h} → Nachbau ${n.x},${n.y} ${n.w}x${n.h})`
      );
    }
  }

  if (abweichungen.length) {
    console.log(`${abweichungen.length} Abweichung(en) bei ${geprueft} gemessenen Komponenten:`);
    abweichungen.forEach((a) => console.log(a));
  } else {
    console.log(`Keine Abweichung ueber ${TOLERANZ}px bei ${geprueft} gemessenen Komponenten.`);
  }
})();
