#!/usr/bin/env node
/**
 * Every internal link in dist/ has to land on a page, and every #fragment on
 * an element with that id.
 *
 *   npm run build && npm run check:links
 *
 * The sync script audits links inside the synced markdown; this audits what
 * the pages themselves link to. The pages deep-link into synced docs by
 * heading anchor (/docs/features/#7-money-that-cant-run-away), and a heading
 * reworded upstream breaks that link silently on the next sync — the page
 * still renders, the browser just stops scrolling. This is where it shows.
 */
import { readFile, readdir, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DIST = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", process.env.DIST ?? "dist");

async function* htmlFiles(dir) {
  for (const name of await readdir(dir)) {
    const p = path.join(dir, name);
    if ((await stat(p)).isDirectory()) yield* htmlFiles(p);
    else if (name.endsWith(".html")) yield p;
  }
}

/** The file a site route is served from, under the directory build format. */
function fileFor(route) {
  const clean = decodeURIComponent(route.split("#")[0].split("?")[0]);
  if (clean.endsWith("/")) return path.join(DIST, clean, "index.html");
  if (path.extname(clean)) return path.join(DIST, clean);
  return path.join(DIST, clean, "index.html");
}

const idCache = new Map();
async function idsOf(file) {
  if (!idCache.has(file)) {
    const html = await readFile(file, "utf8");
    idCache.set(file, new Set([...html.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])));
  }
  return idCache.get(file);
}

if (!existsSync(DIST)) {
  console.error(`\n  no ${DIST} — run npm run build first\n`);
  process.exit(1);
}

const bad = [];
let checked = 0;
for await (const file of htmlFiles(DIST)) {
  const html = await readFile(file, "utf8");
  const page = "/" + path.relative(DIST, file).replace(/index\.html$/, "");
  for (const m of html.matchAll(/\shref="([^"]+)"/g)) {
    let href = m[1].replace(/&amp;/g, "&");
    if (/^(https?:|mailto:|data:)/.test(href)) continue;
    if (href.startsWith("#")) href = page + href;
    if (!href.startsWith("/")) continue;
    checked++;
    const target = fileFor(href);
    if (!existsSync(target)) {
      bad.push(`${page} -> ${href} (no page)`);
      continue;
    }
    const frag = href.includes("#") ? decodeURIComponent(href.split("#")[1]) : "";
    if (frag && target.endsWith(".html") && !(await idsOf(target)).has(frag)) {
      bad.push(`${page} -> ${href} (no #${frag} on that page)`);
    }
  }
}

if (bad.length) {
  console.error(`\n  ${bad.length} broken internal link(s) of ${checked}:\n`);
  for (const b of [...new Set(bad)].sort()) console.error("   ", b);
  console.error("");
  process.exit(1);
}
console.log(`\n  ${checked} internal links, all resolve.\n`);
