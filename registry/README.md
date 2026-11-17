# yaaf marketplace registry

Roles and projects people share for [yaaf](https://github.com/dominicplouffe/yaaf).
Anyone publishes; a moderator's merge is the approval. The format is in
[SPEC.md](SPEC.md) and what is accepted is in [GUIDELINES.md](GUIDELINES.md).

This folder is built to become its own repository, `yaaf-marketplace`:

```bash
git subtree split --prefix=registry -b marketplace
git push git@github.com:<owner>/yaaf-marketplace.git marketplace:main
```

## Publishing

From yaaf: a project's **Settings → Share**, or **Roles → Publish**. yaaf
prepares the listing, signs you in with GitHub once, and opens the pull request
for you. From a terminal: `yaaf publish project <slug>` or `yaaf publish role <slug>`.

By hand: add `listings/<your-github-login>/<slug>/listing.json` and
`versions/1.json`, then run the same checks CI runs:

```bash
pip install jsonschema
python tools/check.py                 # add yaaf to the same venv to run its validators too
```

## Moderating

The queue is the open pull requests. Every PR gets one review card from the
bot: what it is, what it can do, risk flags, the fire drill, and for an update
only the diff. Approving is merging. Listings that can run commands while
holding a key, that add either in an update, or that come from a first-time
publisher need two approvals.

Removal never deletes: set `status` to `removed` with a `status_reason` in
`listing.json`. Every install shows the reason, and new installs are refused.

## What people see besides the listing

- **Installs** (`counts.json`): from CloudFront's logs of listing files being
  downloaded, one address once a day per listing (`tools/count_installs.py`).
  yaaf sends no telemetry.
- **Outcomes** (`outcomes.json`): a project started from a listing may choose,
  once, to report how it went. yaaf opens an `Outcome:` issue here with numbers
  from its receipt only. `tools/outcomes.py` counts them nightly
  (`.github/workflows/outcomes.yml`), ignoring the publisher's own reports and
  counting each account once per listing.
- **No star ratings.** They are the easiest number to fake.

## Layout

```
SPEC.md GUIDELINES.md MODERATORS registry.json
schema/        listing and version JSON schemas
listings/      <handle>/<slug>/listing.json and versions/<n>.json
tools/         check.py · build_index.py · review_card.py · import_yaaf.py
tests/         attacks on every rule the tools enforce
```

Listings are licensed by their publishers (`license` in each `listing.json`).
The tools are Apache-2.0.
