// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";
import { SITE_URL } from "./src/site.config.mjs";

export default defineConfig({
  site: SITE_URL,
  // Every internal link the site emits ends in a slash, so the CloudFront
  // function has one canonical shape to handle.
  trailingSlash: "always",
  // 'directory' gives clean URLs (/why/ not /why.html). See README: the
  // CloudFront Function in infra/ appends index.html for directory requests,
  // because an S3 REST origin will not do it for you.
  build: { format: "directory", inlineStylesheets: "auto" },
  integrations: [sitemap({ filter: (page) => !page.includes("/404") })],
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
