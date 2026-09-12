/**
 * CloudFront Function, runtime cloudfront-js-2.0, on VIEWER REQUEST.
 *
 * An S3 REST origin has no concept of a directory index, so `/why/` 403s
 * without this. (An S3 *website* endpoint would handle it, but that needs a
 * world-readable bucket and an unencrypted origin hop.)
 *
 * CloudFront Functions are JS 5.1-ish: no async, no fetch, no replaceAll,
 * 1ms of CPU. Keep it to string primitives.
 */
function handler(event) {
  var request = event.request;
  var uri = request.uri;

  // The normal case: Astro builds with trailingSlash 'always'.
  if (uri.endsWith('/')) {
    request.uri = uri + 'index.html';
    return request;
  }

  // A hand-typed or externally-linked '/why' — redirect so there is exactly
  // one canonical URL per page rather than two cache entries for one document.
  // A dot in the last segment means a real file (/og.png, /_astro/x.css).
  var last = uri.substring(uri.lastIndexOf('/') + 1);
  if (last.indexOf('.') === -1) {
    return {
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: { location: { value: uri + '/' } },
    };
  }

  return request;
}
