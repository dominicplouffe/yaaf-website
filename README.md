# yaaf-website

The public site for [yaaf](https://github.com/dominicplouffe/yaaf) — a static
Astro build that deploys to S3 behind CloudFront.

```bash
npm install
npm run sync      # pull content out of ../yaaf (only when yaaf changes)
npm run dev       # http://localhost:4321
npm run build     # -> dist/
npm run check:links   # every internal link and #anchor in dist/ resolves
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

`scripts/sync-content.mjs` does these things worth knowing about:

| | |
|---|---|
| **Frontmatter** | yaaf's markdown has none. The leading `# H1` becomes `title`, is stripped from the body (two `<h1>`s on a page is an a11y bug), and frontmatter is injected on write. |
| **Link rewriting** | Happens at sync time, not render time, so a broken link shows up in `git diff` rather than at render. `MCP_SERVER.md` → `/docs/mcp-server/`, `07-foo.md` → `/examples/07-foo/`, and links into the Python package → GitHub. |
| **Example cards** | Each `examples/NN-*.md` has the same skeleton (`**What you get:**`, `**What it costs:**`, `**What you need:**`, and the *"Why not just a Claude Skill?"* blockquote). Those are parsed into frontmatter so the cards are data, not 12 hand-written blurbs. |
| **Screenshots** | The originals (2880px) go to `src/assets/` for `astro:assets`; a 1440px webp of each goes to `public/screenshots/` for the rendered docs, which reference a plain URL. |
| **Specs** | Every example's importable `.json` bundle is copied to `public/setups/`, so an example is actionable from the site whether or not the reader can reach the repository. |
| **Pointer docs** | `docs/GOAL_GRAMMAR.md` is only a pointer to `yaaf/founder/GOAL_GRAMMAR.md`, which has to live beside the code that reads it. The site publishes the rubric itself under the same slug. |
| **Runtimes** | `scripts/export-runtimes.py` loads yaaf's harness, provider and model registries (they import nothing yaaf depends on, so the system `python3` can) plus the CLI pins in the sandbox Dockerfile, and writes `src/content/runtimes.json`. The Runtimes page is generated from it. |
| **Tests** | The test count is collected with `pytest --collect-only` from `../yaaf/.venv` when it exists, and kept from the last sync when it doesn't. |
| **Drills** | Two real `yaaf rehearse` reports on example 06 — as shipped, and with the five authority switches handed back — go to `src/content/drills/`. Needs the same `.venv`. The capacity line moves with the clock, so expect a one-line diff there on every sync; no page shows it. |
| **History** | First commit, commit count, active days and the share co-authored with Claude Code come from `git`. **The sync refuses a shallow clone**: a depth-50 checkout once made the site say the history began on 30 August, when it began on 14 August. Run `git fetch --unshallow` in `../yaaf`. |
| **Link audit** | Fails closed on a link that still points at the repo layout, or at a `/docs/` or `/examples/` page that was never synced. |

`src/content/manifest.json` records the counts and the sync date; the footer
renders them, so a surprising sync is visible on the page.

> **Counts come from the files, never from prose.** The `yaaf` README's own
> figures have drifted more than once (roles, crews, the test count). The site
> counts `src/content/roles/*.json` at build time, and everything else the pages
> state about the repository comes from the manifest.

## The marketplace

`/marketplace/` lists roles and projects people publish for yaaf. Its data is
the registry in `registry/` (format: `registry/SPEC.md`), which is built to
become its own repository, `yaaf-marketplace`, with one command
(`registry/README.md`).

```bash
npm run sync:marketplace   # registry/ -> public/marketplace/ (committed)
```

`public/marketplace/index.json` is served at
`https://yaaf.dplouffe.ca/marketplace/index.json`, the address every yaaf
install reads by default (`YAAF_LIBRARY_SOURCES`). It is regenerated from the
listings, never edited, and CI fails if it differs from a fresh build. The
pages read the same files, so the site never shows a listing yaaf would not
install. **Open in yaaf** is a plain link to `/#/library/install` on the
visitor's own install (`localhost:24247` unless they set another address,
remembered in their browser only), so the site still makes no requests.

`registry/tools/import_yaaf.py` republishes yaaf's own roles and examples as
`@yaaf` listings: a new version only when what a listing installs changed.

## Configuration

Everything that is a decision rather than content is in **`src/site.config.mjs`**:

- `SITE_URL` — canonical origin. Feeds `<link rel=canonical>`, OG tags, the
  sitemap and `robots.txt`. It is `https://yaaf.dplouffe.ca`, the same host as
  the `SITE_HOST` deploy variable; if the domain changes, change this line and
  `public/robots.txt` together.
- `SOURCE_IS_PUBLIC` — set `false` while `dominicplouffe/yaaf` is private and
  every GitHub CTA becomes a "get notified" CTA instead of a 404.
- `SHOW_COMPARE` — `false` for now: the Compare page, its nav item, the home
  page's comparison and the FAQ's Paperclip answer are hidden. The comment on
  the flag says the three steps to bring them back.
- `NAV`, `MORE`, `DOCS_GROUPS` — navigation, the footer's reference links, and
  the docs sidebar order.

## Design

**A public register: registry paper, registrar's ink, and one seal.** yaaf's
product is accountability, so the site reads like an institution you would
trust with authority, not like a launch. Light (Registry `#F4F4F1`) is the
default; dark follows `prefers-color-scheme` and sits on neutral Carbon
`#121316`. No gradients, no glows, no avatars: agents are seats, shown by role.

Three rules hold everywhere:

1. **Seal is only the checker's signature.** The crimson (`--yaaf-seal`) is in
   the logo, on the word "checked" in the home page's first line, and on the
   name after "checked by" in a receipt (`.signed`). Never a button, a link, a
   status, an error or decoration. Headline emphasis is an ink italic (`<em>`).
2. **Primary actions are ink; links and focus are Registrar Blue**
   (`--yaaf-accent`).
3. **The wordmark is never typed.** `Logo` inlines the brand's outlined paths.

**Tokens.** `src/styles/tokens.css` is the brand's generated file, copied in
unedited: use the `--yaaf-*` variables. `src/styles/global.css` imports it and
holds the shared grammar. Tailwind 4 is CSS-first and wired through Vite.

**Type.** Brygada 1918 for headlines, Public Sans for text, IBM Plex Mono for
every number, ID and code sample (all SIL OFL, self-hosted from
`public/fonts/` with their licences). `src/styles/fonts.css` declares only the
weights the site sets, plus metric-matched system fallbacks so nothing
re-wraps when a font arrives. 12px is the floor; headlines are sentence case.
The site makes **no external requests at all**.

**Devices, each used only with its meaning:**

| | |
|---|---|
| `.double-rule` | Final, checked: the end of the hero, under a shipped release, closing the manifesto's commitments, the footer signature. |
| Receipt | Result, made by, checked by, cost. Real text, never an image. |
| Hard-stop meter | Budgets and dates: an ink fill and an ink tick at the wall. |
| `§` marks | Section numbering (`Section` adds the mark to its eyebrow). |
| `Icon` | The twelve line icons in `src/assets/brand/icons/`, 1.75 stroke on a 24px grid. |

Brand assets the site serves live in `public/` (favicons, `og.png`,
`site.webmanifest`, fonts) and `src/assets/brand/` (logo, icons, product
screens). `og.png` is the brand's own artwork; replace the file to change it.

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
| `SITE_HOST` | variable | `yaaf.dplouffe.ca` |

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

Short, plain English. One idea per sentence. If a sentence can lose words, it
should. Long explanations belong in the docs, not on the marketing pages.

Lead with why, then the company. The home page opens on the manifesto's
founding belief, **"Great ideas deserve great teams."**, and is ordered around
five messages: why yaaf exists, how it works, your level of control, why trust
it, and what becomes possible. A first-time visitor should know within one screen that
with yaaf **they build a company, hire a CEO and a team, and chair it**, and
that yaaf is **the harness for teams of harnesses**: Claude Code, Codex, Gemini
CLI and the rest each drive one agent, and yaaf is the harness around the whole
team. "Harness" is the one technical word the home page uses on purpose,
because the reader already knows it; "server", "API" and "policy" still belong
on the docs and How it works pages.

yaaf is open-source software you run, not a service. No "try it free", "sign
up", "plans" or "get started for free": there is nothing to sign up for and
nothing to upgrade to. The rehearsal costs $0 because it calls no model, and
the site says that, not "free trial".

Four rules, because they are why it doesn't read like every other landing page:

1. **Prefer the repo's own sentences.** The yaaf README, the CONTRIBUTING house
   rules and the screenshot alt text are already better copy than anything
   invented for a marketing page.
2. **Every claim maps to a mechanism in the code.** No adjective doing a verb's job.
3. **Numbers are generated, not typed.** If a count can come from
   `getCollection()`, it does.
4. **Never "revolutionary", "seamless", "powerful", "cutting-edge".**

**The manifesto is the exception that proves rule 2.** `/manifesto/` carries
the manifesto's text word for word (the PDF is `public/yaaf-manifesto.pdf`), and
a manifesto is allowed to say what it hopes. So every chapter ends with an
*In yaaf today* line that says which part the code already enforces and which
part it does not yet. Autonomous businesses are the long view, on that page and
on the home page, never a feature.

## Layout

```
src/
  site.config.mjs      every decision that isn't content
  content.config.ts    collection schemas (roles, crews, examples, docs)
  styles/              tokens.css (brand, generated), fonts.css, global.css (shared grammar)
  content/             generated by npm run sync — committed
  assets/screenshots/  2880px originals, processed by astro:assets (reset by every sync)
  assets/brand/        logo, icons and product screens from the brand handoff
  components/          CompanyChart, TeamDiagram, AutonomyDial, OrgChart, RoleCard, Shot, Term, Drill, Section, Nav, Foot
  layouts/             BaseLayout, DocsLayout
  pages/               index, manifesto, how-it-works, features, runtimes (Harnesses), faq,
                       changelog, org, marketplace/, docs, 404; _compare is hidden
                       while SHOW_COMPARE is off, and /why/ redirects to /manifesto/
scripts/
  sync-content.mjs     the content pipeline
  export-runtimes.py   yaaf's runtime registries -> src/content/runtimes.json
  check-links.mjs      internal links and anchors in dist/
  deploy.sh            build -> s3 -> invalidate
infra/
  rewrite-index.js     CloudFront Function: directory index + canonical slash
```

Apache-2.0, same as yaaf.
