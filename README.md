# yaaf-website

The public site for [yaaf](https://github.com/dominicplouffe/yaaf) — a static
Astro build that deploys to S3 behind CloudFront.

```bash
npm install
npm run sync      # pull content out of ../yaaf (only when yaaf changes)
npm run dev       # http://localhost:4321
npm run build     # -> dist/
```

---

## How content gets here

yaaf lives in a **different repository**, so the role library, the crews, the
examples, the docs and the screenshots are copied in by `npm run sync` and the
result is **committed**.

That is deliberate. `npm run build` then touches nothing outside this repo — no
network, no sibling checkout, no credential for a repo that is still private. CI
builds the same bytes a reviewer read in the diff.

```bash
npm run sync                       # reads ../yaaf
YAAF_REPO=~/src/yaaf npm run sync  # reads somewhere else
```

`scripts/sync-content.mjs` does five things worth knowing about:

| | |
|---|---|
| **Frontmatter** | yaaf's markdown has none. The leading `# H1` becomes `title`, is stripped from the body (two `<h1>`s on a page is an a11y bug), and frontmatter is injected on write. |
| **Link rewriting** | Happens at sync time, not render time, so a broken link shows up in `git diff` rather than at render. `MCP_SERVER.md` → `/docs/mcp-server/`, `07-foo.md` → `/examples/07-foo/`, and links into the Python package → GitHub. |
| **Example cards** | Each `examples/NN-*.md` has the same skeleton (`**What you get:**`, `**What it costs:**`, `**What you need:**`, and the *"Why not just a Claude Skill?"* blockquote). Those are parsed into frontmatter so the cards are data, not 12 hand-written blurbs. |
| **Screenshots** | The originals (2880px) go to `src/assets/` for `astro:assets`; a 1440px webp of each goes to `public/screenshots/` for the rendered docs, which reference a plain URL. |
| **Specs** | Every example's importable `.json` bundle is copied to `public/setups/`, so an example is actionable from the site whether or not the reader can reach the repository. |

`src/content/manifest.json` records the counts and the sync date; the footer
renders them, so a surprising sync is visible on the page.

> **Counts come from the files, never from prose.** The `yaaf` README's own
> figures have drifted (it says 34 roles and 14 crews; there are 38 and 17). The
> site counts `src/content/roles/*.json` at build time instead.

## Configuration

Everything that is a decision rather than content is in **`src/site.config.mjs`**:

- `SITE_URL` — canonical origin. Feeds `<link rel=canonical>`, OG tags, the
  sitemap and `robots.txt`. **Currently a placeholder** (`https://yaaf.dev`);
  change this one line when the domain is settled, and update `public/robots.txt`.
- `SOURCE_IS_PUBLIC` — set `false` while `dominicplouffe/yaaf` is private and
  every GitHub CTA becomes a "get notified" CTA instead of a 404.
- `NAV`, `DOCS_GROUPS` — navigation and the docs sidebar order.

## Design

The palette, the 8px radius, the hairline borders and the mono uppercase
eyebrows are lifted from the product's own cockpit CSS (`yaaf/web/src/styles.css`)
so the site and the app read as one thing. Tokens live in an `@theme` block in
`src/styles/global.css` — Tailwind 4 is CSS-first, there is no
`tailwind.config.js`, and the Tailwind plugin is wired through Vite rather than
the deprecated `@astrojs/tailwind` integration.

Fonts are self-hosted through `@fontsource-variable` — the site makes **no
external requests at all**.

### Regenerating the social card

`public/og.png` is rendered from `scripts/og.html` in a real browser, because
rasterising SVG text through sharp resolves fonts via system fontconfig and
silently swaps the typeface on whatever machine runs it.

```bash
npx playwright install chromium   # once
npm run og
```

---

## Deploying

### One-time AWS setup

1. **Bucket** — private. Block Public Access fully on. No website hosting, no
   bucket ACLs.
2. **CloudFront distribution**
   - Origin: the bucket's **REST** endpoint (`<bucket>.s3.<region>.amazonaws.com`),
     origin access = **Origin Access Control**, signing enabled.
   - Bucket policy: allow `s3:GetObject` to `Service: cloudfront.amazonaws.com`
     conditioned on `AWS:SourceArn` = the distribution ARN.
   - Default root object: `index.html`.
   - Viewer protocol policy: redirect to HTTPS. Compress objects automatically: **on**.
   - **Function association** — attach `infra/rewrite-index.js` on *viewer
     request*. An S3 REST origin has no directory index, so `/why/` 403s without it.
   - **Custom error responses** — `403 → /404.html (404)` **and** `404 → /404.html (404)`.
     The 403 mapping is the non-obvious one: with OAC, S3 returns 403 for a
     missing key, so without it every typo renders raw `AccessDenied` XML.
   - ACM certificate for the domain, issued in **us-east-1**.
3. **OIDC for GitHub Actions**
   - An identity provider for `token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
   - A role whose trust policy pins
     `token.actions.githubusercontent.com:sub` to
     `repo:dominicplouffe/yaaf-website:environment:production`.
   - Permissions: `s3:ListBucket` on the bucket; `s3:GetObject`,
     `s3:PutObject`, `s3:DeleteObject` on `bucket/*`;
     `cloudfront:CreateInvalidation` and `cloudfront:GetInvalidation` on the
     distribution. Nothing else.

### Repository settings

| Name | Kind | Example |
|---|---|---|
| `AWS_DEPLOY_ROLE_ARN` | secret | `arn:aws:iam::123456789012:role/yaaf-website-deploy` |
| `CLOUDFRONT_DISTRIBUTION_ID` | secret | `E123456789ABC` |
| `AWS_REGION` | variable | `us-east-1` |
| `S3_BUCKET` | variable | `yaaf-website-prod` |
| `SITE_HOST` | variable | `yaaf.dev` |

There are no AWS access keys anywhere. That is the point of OIDC.

### Deploying

Push to `main` and `.github/workflows/deploy.yml` does it. By hand:

```bash
S3_BUCKET=yaaf-website-prod \
CLOUDFRONT_DISTRIBUTION_ID=E123456789ABC \
./scripts/deploy.sh
```

`scripts/deploy.sh` uploads in three passes that partition the key space
exactly — immutable for `/_astro/*`, a day for other assets, revalidate for
HTML — then sweeps anything the build no longer emits, then invalidates and
waits. Uploads happen before deletes, so no HTML in flight ever points at an
asset that is already gone.

---

## Writing for this site

Four rules, because they are why it doesn't read like every other landing page:

1. **Prefer the repo's own sentences.** The yaaf README, the CONTRIBUTING house
   rules and the screenshot alt text are already better copy than anything
   invented for a marketing page.
2. **Every claim maps to a mechanism in the code.** No adjective doing a verb's job.
3. **Numbers are generated, not typed.** If a count can come from
   `getCollection()`, it does.
4. **Never "revolutionary", "seamless", "powerful", "cutting-edge".**

## Layout

```
src/
  site.config.mjs      every decision that isn't content
  content.config.ts    collection schemas (roles, crews, examples, docs)
  styles/global.css    the @theme palette and the prose styles
  content/             generated by npm run sync — committed
  assets/screenshots/  2880px originals, processed by astro:assets
  components/          OrgChart, RoleCard, Shot, Term, Section, Nav, Foot
  layouts/             BaseLayout, DocsLayout
  pages/               index, why, org, examples, docs, 404
scripts/
  sync-content.mjs     the content pipeline
  deploy.sh            build -> s3 -> invalidate
  make-og.mjs, og.html the social card
infra/
  rewrite-index.js     CloudFront Function: directory index + canonical slash
```

Apache-2.0, same as yaaf.
