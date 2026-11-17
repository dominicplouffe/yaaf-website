# The yaaf registry format, version 1

A registry is a folder of listings and one generated `index.json`. yaaf reads
any registry that follows this file; the official one is the marketplace, and a
company can run its own by copying this folder.

## Names

A listing is `@handle/slug`.

- `handle` is the publisher's GitHub login, lowercased. A pull request may only
  add or change listings under its author's handle. `@yaaf` is reserved for the
  library that ships with yaaf.
- `slug` matches `^[a-z0-9-]{2,64}$`, the same rule yaaf applies to role slugs.

## Layout

```
listings/<handle>/<slug>/listing.json        what the listing is (editable)
listings/<handle>/<slug>/versions/<n>.json   what gets installed (never edited)
index.json                                   generated, never committed by hand
```

A version file is immutable once merged. A change is a new version. The checks
refuse an edit to a merged version file.

## listing.json

| field | | |
|---|---|---|
| `id` | required | `@handle/slug`, matching its folder |
| `kind` | required | `role` or `project` |
| `name` | required | what people call it |
| `summary` | required | one sentence, the outcome, 160 characters or fewer |
| `category` | required | `leadership`, `research`, `build`, `content`, `challenge` or `growth` |
| `domains` | required | free slugs, e.g. `["markets"]` |
| `license` | required | `CC-BY-4.0` or `Apache-2.0` |
| `status` | required | `active`, `deprecated` or `removed` |
| `status_reason` | when not active | shown to everyone who installed it |
| `forked_from` | optional | `{"id": "@handle/slug", "version": n}` |
| `details` | optional | `what_you_get`, `what_it_costs`, `what_you_need`: one paragraph each |

## A version file

```json
{
  "id": "@yaaf/blog-writer",
  "version": 1,
  "kind": "role",
  "published_at": "2026-11-14",
  "changes": "First version.",
  "role": { "...": "exactly what POST /admin/roles accepts" },
  "needs": { "keys": [], "data_sources": [], "mailbox": false, "github_repo": false }
}
```

A project version carries `bundle` instead of `role`: a yaaf setup file
(`yaaf_bundle: 1`, `kind: project_setup`) with `values_included: false` and no
secret values anywhere. Roles the project hires travel in `bundle.roles` as full
definitions, and `uses` lists the ones that are listings of their own:

```json
"uses": [{ "id": "@yaaf/researcher", "version": 1, "slug": "researcher" }]
```

### needs

What the person installing must bring. Never a value.

```json
"keys": [{
  "name": "wordpress",                 // the yaaf credential name; the prompt reads $WORDPRESS
  "label": "WordPress application password",
  "format": "username:application-password",
  "file": false,                       // true when the credential is a file
  "roles": ["blog-writer"],            // which roles receive it
  "required": false,                   // optional only if the prompt says what to do without it
  "help": "https://wordpress.org/documentation/article/application-passwords/"
}],
"data_sources": [{
  "name": "ads",                       // agents call its tools as mcp__ads__<tool>; never renamed
  "serves": "Google Ads reporting",
  "address": "bring-your-own",         // or the https address of a public server
  "auth": "none" | "bearer" | "oauth",
  "access": "inline" | "bulk",
  "tools": ["search_stream"],          // the allow list; every other tool is denied
  "roles": ["ppc-analyst"],
  "required": true
}],
"mailbox": false,
"github_repo": false
```

### inputs (projects only)

The blanks the Founder asks for at install. A blank appears in the goal, the
standing orders or a team name as `{{id}}`.

```json
"inputs": [{
  "id": "business",                    // ^[a-z][a-z0-9_]{1,31}$
  "question": "What is the business called?",
  "type": "text" | "url" | "domain" | "number" | "money" | "choice" | "list",
  "choices": ["..."],                  // type choice only
  "example": "Northwind Outfitters",   // never the publisher's own value
  "required": true
}]
```

Role versions never have inputs. A role in a library serves many projects, so
anything specific to one project belongs in that project's standing orders.

### receipt (projects only, optional)

The publisher's yaaf receipt, as `GET /admin/projects/{id}/receipt` returns its
`project`, `cost` and `verified` parts. Shown as reported by the publisher's
install.

## index.json

Built by `tools/build_index.py` on every merge.

```json
{
  "registry": {
    "spec": 1,
    "name": "yaaf marketplace",
    "publish": { "method": "github-pr", "repo": "owner/repo", "client_id": null }
  },
  "generated_at": "2026-11-14T12:00:00Z",
  "listings": [{
    "...": "everything in listing.json",
    "tier": "official" | "community",
    "latest": 2,
    "versions": [{
      "version": 2,
      "path": "listings/yaaf/blog-writer/versions/2.json",
      "sha256": "…",                   // of the file's bytes, as served
      "published_at": "2026-11-14",
      "changes": "…",
      "can_do": ["bash", "files", "web"],
      "keys": ["wordpress"],
      "data_sources": [],
      "inputs": []
    }],
    "installs": 0
  }]
}
```

Paths are relative to the index's own URL. yaaf refuses a version whose bytes
do not hash to `sha256`, and refuses to hire a listing whose status is `removed`.
