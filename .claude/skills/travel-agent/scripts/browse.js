#!/usr/bin/env node
/**
 * Render a page in headless Chromium and print what a person would see.
 *
 * Why: flight and hotel sites build their results with JavaScript, so curl and the
 * WebFetch tool get an empty shell. A real browser run waits for the results to load.
 * It goes out through the session proxy (HTTPS_PROXY) because WebFetch does not.
 *
 * Usage:
 *   node browse.js <url> [--wait 8000] [--scroll 3] [--max 6000] [--shot out.png]
 *                        [--click "text=Accept"] [--prices]
 *   --wait    ms to wait after load for results to appear (default 8000)
 *   --scroll  number of page-down scrolls to trigger lazy loading (default 3)
 *   --max     max characters of page text to print (default 6000)
 *   --shot    save a screenshot to this path
 *   --click   extra selector to click before reading (repeatable), e.g. a cookie button
 *   --prices  print only lines that contain a currency amount (plus a little context)
 *
 * Output is JSON: {url, finalUrl, status, title, blocked, text|priceLines}.
 * `blocked: true` means the page looks like a bot check or captcha; report it, don't
 * try to get around it.
 */
const { chromium } = require('playwright');

function parse(argv) {
  const o = { url: null, wait: 8000, scroll: 3, max: 6000, shot: null, click: [], prices: false };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--wait') o.wait = +argv[++i];
    else if (a === '--scroll') o.scroll = +argv[++i];
    else if (a === '--max') o.max = +argv[++i];
    else if (a === '--shot') o.shot = argv[++i];
    else if (a === '--click') o.click.push(argv[++i]);
    else if (a === '--prices') o.prices = true;
    else if (!o.url) o.url = a;
  }
  return o;
}

const COOKIE_BUTTONS = [
  'button:has-text("Accept all")', 'button:has-text("Accept All")', 'button:has-text("Accept")',
  'button:has-text("I agree")', 'button:has-text("Agree")', 'button:has-text("Got it")',
  '#onetrust-accept-btn-handler', 'button:has-text("Allow all")',
];
const BOT_HINTS = /captcha|are you a robot|verify you are human|unusual traffic|access denied|pardon the interruption|press (&|and) hold/i;
const PRICE = /(£|€|\$|\b(?:GBP|EUR|USD)\b)\s?\d|\d[\d,\.]*\s?(£|€|\b(?:GBP|EUR|USD)\b)/;

(async () => {
  const o = parse(process.argv);
  if (!o.url) { console.error('usage: node browse.js <url> [options]'); process.exit(2); }

  const opts = {};
  if (process.env.HTTPS_PROXY) opts.proxy = { server: process.env.HTTPS_PROXY };
  const browser = await chromium.launch(opts);
  const ctx = await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    locale: 'en-GB', viewport: { width: 1366, height: 900 },
  });
  const page = await ctx.newPage();
  const out = { url: o.url };
  try {
    const resp = await page.goto(o.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    out.status = resp ? resp.status() : null;
    for (const sel of COOKIE_BUTTONS) {            // best effort, harmless if absent
      try { await page.click(sel, { timeout: 800 }); break; } catch (_) {}
    }
    for (const sel of o.click) { try { await page.click(sel, { timeout: 3000 }); } catch (_) {} }
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(o.wait);
    for (let i = 0; i < o.scroll; i++) { await page.keyboard.press('PageDown'); await page.waitForTimeout(600); }
    out.finalUrl = page.url();
    out.title = await page.title();
    const text = (await page.evaluate(() => document.body ? document.body.innerText : '')).replace(/\n{3,}/g, '\n\n');
    // A 403/429 or a bot-check wording both mean the site refused us, even if the page renders.
    out.blocked = (out.status === 403 || out.status === 429 || out.status === 401)
      || BOT_HINTS.test(text.slice(0, 3000)) || BOT_HINTS.test(out.title || '');
    if (o.prices) {
      const lines = text.split('\n'); const keep = new Set();
      lines.forEach((l, i) => { if (PRICE.test(l)) for (let k = Math.max(0, i - 2); k <= Math.min(lines.length - 1, i + 1); k++) keep.add(k); });
      out.priceLines = [...keep].sort((a, b) => a - b).map(i => lines[i].trim()).filter(Boolean).slice(0, 150);
      out.priceCount = out.priceLines.length;
    } else {
      out.text = text.slice(0, o.max);
      out.truncated = text.length > o.max;
    }
    if (o.shot) await page.screenshot({ path: o.shot, fullPage: false });
  } catch (e) {
    out.error = String(e.message || e).split('\n')[0];
  } finally {
    await browser.close();
  }
  console.log(JSON.stringify(out, null, 2));
})();
