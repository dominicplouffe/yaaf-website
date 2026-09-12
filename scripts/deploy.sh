#!/usr/bin/env bash
#
# Build and publish dist/ to S3, then invalidate CloudFront.
#
#   S3_BUCKET=yaaf-website-prod \
#   CLOUDFRONT_DISTRIBUTION_ID=E123456789ABC \
#   ./scripts/deploy.sh
#
# The three upload passes partition the key space exactly:
#
#   1. _astro/*                      fingerprinted by Astro  -> immutable
#   2. everything else that is not   unfingerprinted assets  -> one day
#      *.html / *.xml / *.txt / *.json
#   3. *.html *.xml *.txt *.json     the entry points        -> revalidate
#
# Nothing is in two passes and nothing is in none. That invariant is what
# makes it safe to scope --delete per pass; if you add a fourth filter that
# overlaps, one pass will delete what another just uploaded.
#
# Uploads happen before deletes, so no HTML in flight ever points at an asset
# that has already been removed.
set -euo pipefail

: "${S3_BUCKET:?set S3_BUCKET}"
: "${CLOUDFRONT_DISTRIBUTION_ID:?set CLOUDFRONT_DISTRIBUTION_ID}"

DIST="${DIST:-dist}"
S3="s3://${S3_BUCKET}"

if [ "${SKIP_BUILD:-}" != "1" ]; then
  npm run build
fi

[ -f "${DIST}/index.html" ] || { echo "no ${DIST}/index.html — build first" >&2; exit 1; }
[ -f "${DIST}/404.html" ]   || { echo "no ${DIST}/404.html — CloudFront error pages would break" >&2; exit 1; }

sync() { aws s3 sync "${DIST}/" "${S3}/" --no-progress --only-show-errors "$@"; }

IMMUTABLE="public, max-age=31536000, immutable"
ASSET="public, max-age=86400"
ENTRY="public, max-age=0, must-revalidate"
ENTRIES=(--include "*.html" --include "*.xml" --include "*.txt" --include "*.json")
NOT_ENTRIES=(--exclude "*.html" --exclude "*.xml" --exclude "*.txt" --exclude "*.json")

echo "==> 1/4  fingerprinted assets"
# .avif is split out because the AWS CLI guesses Content-Type from Python's
# mimetypes, which does not reliably know it and will label it octet-stream.
sync --exclude "*" --include "_astro/*" --exclude "_astro/*.avif" --cache-control "${IMMUTABLE}"
sync --exclude "*" --include "_astro/*.avif" --cache-control "${IMMUTABLE}" --content-type "image/avif"

echo "==> 2/4  other static assets"
sync --exclude "_astro/*" "${NOT_ENTRIES[@]}" --cache-control "${ASSET}"

echo "==> 3/4  html, sitemap, robots, example specs"
sync --exclude "*" "${ENTRIES[@]}" --cache-control "${ENTRY}" --delete

echo "==> 4/4  sweep anything the build no longer emits"
sync --exclude "*" --include "_astro/*" --cache-control "${IMMUTABLE}" --delete
sync --exclude "_astro/*" "${NOT_ENTRIES[@]}" --cache-control "${ASSET}" --delete

echo "==> invalidating"
ID="$(aws cloudfront create-invalidation \
  --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
  --paths '/*' --query 'Invalidation.Id' --output text)"
echo "    ${ID}"
aws cloudfront wait invalidation-completed \
  --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" --id "${ID}"

echo "done — https://${SITE_HOST:-$S3_BUCKET}/"
