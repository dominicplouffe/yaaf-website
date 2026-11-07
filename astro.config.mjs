// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";
import { SITE_URL } from "./src/site.config.mjs";

// Pages that existed until the docs were cut back to install, configuration,
// deployment, architecture, providers, CLI and security, and the use-case
// pages built from the example write-ups that went with them. Each lands on
// the nearest page that still exists, so old links and search results work.
const EXAMPLES = [
  "01-your-first-hour", "02-settle-an-argument", "03-a-desk-the-world-wakes",
  "04-an-overnight-crew", "05-a-tutor-that-adapts", "06-a-red-team",
  "07-tell-me-what-changed", "08-a-game-you-can-play", "09-one-idea-thirty-days",
  "10-read-the-filings", "11-numbers-you-can-defend", "12-a-content-engine",
];
const RETIRED = {
  "/examples": "/how-it-works/",
  ...Object.fromEntries(EXAMPLES.map((slug) => [`/examples/${slug}`, "/how-it-works/"])),
  "/docs/runtimes": "/docs/providers/",
  "/docs/mcp-server": "/docs/install/",
  "/docs/creating-a-project": "/docs/install/",
  ...Object.fromEntries(
    ["plan", "features", "governance", "autonomy", "goal-grammar", "dashboard", "agent-api", "integrations", "auth"]
      .map((slug) => [`/docs/${slug}`, "/docs/"]),
  ),
};
const REDIRECTED = ["/why", ...Object.keys(RETIRED)];

export default defineConfig({
  site: SITE_URL,
  // Every internal link the site emits ends in a slash, so the CloudFront
  // function has one canonical shape to handle.
  trailingSlash: "always",
  // 'directory' gives clean URLs (/why/ not /why.html). See README: the
  // CloudFront Function in infra/ appends index.html for directory requests,
  // because an S3 REST origin will not do it for you.
  build: { format: "directory", inlineStylesheets: "auto" },
  // /why/ became /compare/ when the comparison grew past three questions.
  // While SHOW_COMPARE is off (src/site.config.mjs) it lands on the home
  // page's "Why yaaf exists" instead.
  // A static redirect page keeps old links and search results working.
  redirects: { "/why": "/#why", ...RETIRED },
  integrations: [
    sitemap({
      filter: (page) => !page.includes("/404") && !REDIRECTED.some((from) => page.endsWith(`${from}/`)),
    }),
  ],
  vite: { plugins: [tailwindcss()] },
  markdown: {
    shikiConfig: {
      theme: "github-dark-default",
      // DEPLOYMENT.md has one ```caddy fence and shiki has no caddy grammar.
      langAlias: { caddy: "nginx" },
      wrap: false,
    },
  },
  image: {
    // Screenshots are 2880px-wide retina captures. Never emit a variant at
    // that size — the AVIF encode is the slowest thing in the build and
    // nothing on the page is ever that wide.
    breakpoints: [480, 640, 960, 1280, 1600],
    responsiveStyles: true,
  },
});
