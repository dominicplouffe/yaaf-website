#!/usr/bin/env node
/**
 * Pull content out of the yaaf repo and into this one.
 *
 * yaaf is a separate repository, so the site would otherwise either vendor a
 * hand-maintained copy (which drifts) or fetch at build time (which makes the
 * build depend on a network and on that repo being public). Neither is good.
 * Instead: this script copies, the result is committed, and `astro build`
 * touches nothing outside this repo.
 *
 *   npm run sync                 # reads ../yaaf
 *   YAAF_REPO=/path npm run sync # reads somewhere else
 *
 * Re-run it whenever yaaf changes and commit the diff.
 */
import { readFile, writeFile, mkdir, rm, readdir, copyFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SITE = path.resolve(HERE, "..");
const SRC = path.resolve(process.env.YAAF_REPO ?? path.join(SITE, "..", "yaaf"));

const OUT = {
  roles: path.join(SITE, "src/content/roles"),
  crews: path.join(SITE, "src/content/crews"),
  examples: path.join(SITE, "src/content/examples"),
  docs: path.join(SITE, "src/content/docs"),
  assets: path.join(SITE, "src/assets/screenshots"),
  public: path.join(SITE, "public/screenshots"),
  setups: path.join(SITE, "public/setups"),
};

/** Docs that are indexes or meta, not pages of their own. */
const SKIP_DOCS = new Set(["README.md"]);

const log = (...a) => console.log("  ", ...a);

function docSlug(filename) {
  return path.basename(filename, ".md").toLowerCase().replace(/_/g, "-");
}

/** yaml-escape a scalar for the frontmatter we inject. */
function y(value) {
  if (value === undefined || value === null) return '""';
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(String(value));
}

/**
 * Rewrite intra-repo links to site routes. Done here rather than in a remark
 * plugin so the committed markdown is already correct and a broken link shows
 * up in a diff instead of at render time.
 */
function rewriteLinks(md, kind) {
  const GH = "https://github.com/dominicplouffe/yaaf";
  return (
    md
      // Order matters: CONTRIBUTING.md and README.md are SHOUTING_CASE too,
      // and neither is a docs page, so they have to be claimed first.
      .replace(/\]\((?:\.\.\/)?CONTRIBUTING\.md(#[^)\s]*)?\)/g, `](${GH}/blob/main/CONTRIBUTING.md$1)`)
      // README.md means the index of whichever set the file lives in. The
      // fragment is dropped: those hubs are composed here, not copied, so an
      // anchor from the repo's own index would not resolve.
      .replace(
        /\]\((?:\.\.\/)?(?:examples\/)?README\.md(?:#[^)\s]*)?\)/g,
        kind === "examples" ? "](/examples/)" : "](/docs/)",
      )
      // docs/FOO.md, ./FOO.md, ../docs/FOO.md  ->  /docs/foo/
      .replace(
        /\]\((?:\.\/|\.\.\/)?(?:docs\/)?([A-Z][A-Z0-9_]*)\.md(#[^)\s]*)?\)/g,
        (_m, name, hash) => `](/docs/${docSlug(name + ".md")}/${hash ?? ""})`,
      )
      .replace(/\]\((?:\.\.\/)?LICENSE\)/g, `](${GH}/blob/main/LICENSE)`)
      // examples/07-foo.md (or a bare sibling 07-foo.md) -> /examples/07-foo/
      .replace(/\]\((?:\.\.\/)?(?:examples\/)?(\d\d-[a-z0-9-]+)\.md(#[^)\s]*)?\)/g, "](/examples/$1/$2)")
      .replace(/\]\((?:\.\.\/)?examples\/[0-9a-z-]+\.json\)/g, "](/examples/)")
      .replace(/\]\((?:\.\.\/)?examples\/\)/g, "](/examples/)")
      // the role library has a page of its own here
      .replace(/\]\((?:\.\.\/)?roles\/?\)/g, "](/org/#roles)")
      // directories and source files that only exist in the repository
      .replace(/\]\(\.\.\/yaaf\/([^)]+)\)/g, `](${GH}/blob/main/yaaf/$1)`)
      .replace(/\]\(\.\.\/(evals|crews|migrations|deploy|tests)\/?\)/g, `](${GH}/tree/main/$1)`)
      // screenshots -> the public copies written by syncScreenshots()
      .replace(/\]\((?:\.\.\/)?(?:docs\/)?screenshots\/([a-z0-9-]+)\.png\)/g, "](/screenshots/$1.webp)")
      .replace(/src="(?:\.\.\/)?(?:docs\/)?screenshots\/([a-z0-9-]+)\.png"/g, 'src="/screenshots/$1.webp"')
      // docs/projects/ is not published here
      .replace(/\[([^\]]+)\]\((?:\.\.\/)?(?:docs\/)?projects\/\)/g, "$1")
  );
}

/** Pull the leading `# Title` off a markdown file. */
function splitTitle(md) {
  const m = md.match(/^\s*#\s+(.+?)\s*$/m);
  if (!m) return { title: null, body: md };
  return { title: m[1], body: md.slice(0, m.index) + md.slice(m.index + m[0].length) };
}

/** Grab a `**Label:** value` line, returning the value with markdown intact. */
function labelled(md, label) {
  const re = new RegExp(`\\*\\*${label}:?\\*\\*\\s*([\\s\\S]*?)(?:\\n\\n|\\n\\*\\*|\\n---)`, "i");
  const m = md.match(re);
  if (!m) return null;
  return m[1]
    .split("\n")
    .map((line) => line.replace(/^\s*>\s?/, ""))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

async function reset(dir) {
  await rm(dir, { recursive: true, force: true });
  await mkdir(dir, { recursive: true });
}

async function syncJson(kind, fromDir, toDir) {
  await reset(toDir);
  const files = (await readdir(fromDir)).filter((f) => f.endsWith(".json")).sort();
  for (const f of files) {
    await copyFile(path.join(fromDir, f), path.join(toDir, f));
  }
  log(`${kind}: ${files.length}`);
  return files.length;
}

/** Root-level markdown that belongs in the docs nav anyway. */
const ROOT_DOCS = ["SECURITY.md"];

async function syncDocs() {
  await reset(OUT.docs);
  const dir = path.join(SRC, "docs");
  const files = (await readdir(dir)).filter((f) => f.endsWith(".md") && !SKIP_DOCS.has(f)).sort();
  const sources = [
    ...files.map((f) => [path.join(dir, f), f, `docs/${f}`]),
    ...ROOT_DOCS.map((f) => [path.join(SRC, f), f, f]),
  ];
  for (const [abs, f, rel] of sources) {
    const raw = await readFile(abs, "utf8");
    const { title, body } = splitTitle(rewriteLinks(raw, "docs"));
    const slug = docSlug(f);
    // The docs have no frontmatter of their own; the H1 is the only title.
    const [name, ...rest] = (title ?? slug).split(/\s+—\s+/);
    const fm = [
      "---",
      `title: ${y(name.trim())}`,
      `subtitle: ${y(rest.join(" — ").trim())}`,
      `slug: ${y(slug)}`,
      `sourceFile: ${y(rel)}`,
      "---",
      "",
    ].join("\n");
    await writeFile(path.join(OUT.docs, `${slug}.md`), fm + body.trimStart() + "\n");
  }
  log(`docs: ${sources.length}`);
  return sources.length;
}

async function syncExamples() {
  await reset(OUT.examples);
  await reset(OUT.setups);
  const dir = path.join(SRC, "examples");
  const files = (await readdir(dir)).filter((f) => /^\d\d-.*\.md$/.test(f)).sort();
  for (const f of files) {
    const raw = await readFile(path.join(dir, f), "utf8");
    const spec = JSON.parse(await readFile(path.join(dir, f.replace(/\.md$/, ".json")), "utf8"));
    const { title, body } = splitTitle(rewriteLinks(raw, "examples"));
    const num = f.slice(0, 2);
    const slug = f.replace(/^\d\d-/, "").replace(/\.md$/, "");
    const project = spec.project ?? {};
    const teams = (project.teams ?? []).map((t) => ({
      name: t.name,
      role: t.role_slug,
      employees: t.employees ?? [],
      lead: t.lead ?? null,
    }));
    const fm = [
      "---",
      `number: ${y(num)}`,
      `title: ${y((title ?? slug).replace(/^\d\d\s*—\s*/, ""))}`,
      `slug: ${y(`${num}-${slug}`)}`,
      `mode: ${y(project.mode ?? "deliver")}`,
      `solo: ${y(Boolean(project.solo))}`,
      `cap: ${y(project.constitution?.monthly_usd_cap ?? null)}`,
      `projectName: ${y(project.name ?? "")}`,
      `whySkill: ${y(labelled(raw, "Why not just a Claude Skill\\?") ?? "")}`,
      `whatYouGet: ${y(labelled(raw, "What you get") ?? "")}`,
      `whatItCosts: ${y(labelled(raw, "What it costs") ?? "")}`,
      `whatYouNeed: ${y(labelled(raw, "What you need") ?? "")}`,
      `spec: ${y(`examples/${f.replace(/\.md$/, ".json")}`)}`,
      `teams: ${JSON.stringify(teams)}`,
      "---",
      "",
    ].join("\n");
    await writeFile(path.join(OUT.examples, `${num}-${slug}.md`), fm + body.trimStart() + "\n");
    // The importable bundle, served as-is, so an example is actionable from
    // the site whether or not the reader can reach the repository.
    await copyFile(
      path.join(dir, f.replace(/\.md$/, ".json")),
      path.join(OUT.setups, f.replace(/\.md$/, ".json")),
    );
  }
  log(`examples: ${files.length}`);
  return files.length;
}

async function syncScreenshots() {
  await reset(OUT.assets);
  await reset(OUT.public);
  const dir = path.join(SRC, "docs/screenshots");
  const files = (await readdir(dir)).filter((f) => f.endsWith(".png")).sort();
  for (const f of files) {
    // Originals go to src/assets for astro:assets to process per-usage.
    await copyFile(path.join(dir, f), path.join(OUT.assets, f));
    // Docs markdown references a plain URL, so write one sane web copy too:
    // the source is a 2880px-wide retina capture and nobody needs that.
    await sharp(path.join(dir, f))
      .resize({ width: 1440, withoutEnlargement: true })
      .webp({ quality: 82 })
      .toFile(path.join(OUT.public, f.replace(/\.png$/, ".webp")));
  }
  log(`screenshots: ${files.length} (originals + 1440px webp)`);
  return files.length;
}

/**
 * Fail closed. A link that still points at the repository's own layout would
 * render as a 404 on the site, and the only place it is cheap to catch is
 * here — once it is committed markdown it looks like content, not a bug.
 */
async function auditLinks() {
  const bad = [];
  for (const dir of [OUT.docs, OUT.examples]) {
    for (const name of await readdir(dir)) {
      const text = await readFile(path.join(dir, name), "utf8");
      for (const m of text.matchAll(/\]\(([^)\s]+)\)/g)) {
        if (/^(https?:|mailto:|#|\/)/.test(m[1])) continue;
        bad.push(`${path.basename(dir)}/${name} -> ${m[1]}`);
      }
    }
  }
  return bad;
}

async function main() {
  if (!existsSync(SRC)) {
    console.error(`\n  yaaf repo not found at ${SRC}`);
    console.error("  Set YAAF_REPO=/path/to/yaaf and re-run.\n");
    process.exit(1);
  }
  console.log(`\nsyncing content from ${SRC}\n`);
  const counts = {
    roles: await syncJson("roles", path.join(SRC, "roles"), OUT.roles),
    crews: await syncJson("crews", path.join(SRC, "crews"), OUT.crews),
    examples: await syncExamples(),
    docs: await syncDocs(),
    screenshots: await syncScreenshots(),
  };
  const bad = await auditLinks();
  if (bad.length) {
    console.error(`\n  ${bad.length} link(s) still point at the repo layout:`);
    for (const b of bad) console.error("   ", b);
    console.error("\n  Add a rule to rewriteLinks() and re-run.\n");
    process.exit(1);
  }

  // A manifest, so pages can state exact counts without re-counting at render
  // time and so a surprising diff is visible in review.
  await writeFile(
    path.join(SITE, "src/content/manifest.json"),
    JSON.stringify({ syncedAt: new Date().toISOString().slice(0, 10), ...counts }, null, 2) + "\n",
  );
  console.log("\ndone.\n");
}

await main();
