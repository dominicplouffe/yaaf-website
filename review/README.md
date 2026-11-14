# Review screenshots

Before/after captures for the rebrand pull requests, one folder per PR.
Files are named `<page>-<scheme>-<viewport width>` (WebP, or JPEG where a
page is too tall for WebP); the 1440px captures are stored at half size.

- The old site had no light theme, so "before" exists in dark only, and
  `01-foundation/before` is the "before" for every later PR too.
- Each PR's `after` holds the pages that PR restyles. The foundation PR
  changes every page through the shared styles; its `after` shows the pages
  where that is the whole change so far, and the rest follow in their own PRs.

This folder is for review only and is not part of the site. Delete it before
the last pull request merges:

```bash
git rm -r review
```
