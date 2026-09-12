#!/usr/bin/env node
/**
 * Render public/og.png from scripts/og.html.
 *
 * Rendered in a real browser rather than rasterised from SVG: sharp's librsvg
 * resolves <text> through system fontconfig, not node_modules, so an SVG route
 * silently swaps the typeface on whatever machine runs it. Chromium uses the
 * same @font-face files the site does, so the card matches the site exactly.
 *
 *   npm run og        # needs `npx playwright install chromium` once
 */
import { chromium } from "playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
await page.goto("file://" + path.join(HERE, "og.html"), { waitUntil: "networkidle" });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(200);
await page.screenshot({ path: path.join(HERE, "..", "public", "og.png") });
await browser.close();
console.log("wrote public/og.png");
