// Build the marketplace's index and served files from registry/.
//
//   npm run sync:marketplace
//
// Runs registry/tools/build_index.py into public/marketplace/, which CloudFront
// serves at /marketplace/index.json: the URL every yaaf install reads by
// default (YAAF_LIBRARY_SOURCES). The output is committed, like every other
// synced file, so `npm run build` needs nothing but this repository and CI
// builds the bytes a reviewer read. CI rebuilds it and fails on any difference.

import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SITE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(SITE, "public/marketplace");
const python = process.env.PYTHON ?? "python3";

execFileSync(python, [path.join(SITE, "registry/tools/build_index.py"), "--out", OUT], { stdio: "inherit" });

// generated_at moves on every build. Pin it to the newest version date so a
// rebuild of unchanged listings is byte-identical and CI can compare.
const indexPath = path.join(OUT, "index.json");
const index = JSON.parse(readFileSync(indexPath, "utf8"));
const newest = index.listings.flatMap((l) => l.versions.map((v) => v.published_at)).sort().at(-1);
index.generated_at = `${newest ?? "1970-01-01"}T00:00:00Z`;
writeFileSync(indexPath, JSON.stringify(index, null, 1) + "\n");
console.log(`marketplace: ${index.listings.length} listings → public/marketplace/`);
