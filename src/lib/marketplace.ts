/**
 * The marketplace's data, as the pages read it: public/marketplace/, which
 * `npm run sync:marketplace` builds from registry/ and every yaaf install
 * downloads from. One source, so the site never shows a listing yaaf would not
 * install.
 */
import index from "../../public/marketplace/index.json";
import { SITE_URL } from "../site.config.mjs";

/** The URL yaaf installs read by default (YAAF_LIBRARY_SOURCES). */
export const INDEX_URL = `${SITE_URL}/marketplace/index.json`;
export const REGISTRY_REPO = "https://github.com/dominicplouffe/yaaf-marketplace";

export interface VersionEntry {
  version: number;
  path: string;
  sha256: string;
  published_at: string;
  changes: string;
  can_do: string[];
  keys: string[];
  required_keys: string[];
  data_sources: string[];
  mailbox: boolean;
  github_repo: boolean;
  inputs: string[];
  roles: string[];
  has_receipt: boolean;
}

export interface Listing {
  id: string;
  kind: "role" | "project";
  name: string;
  summary: string;
  category: string;
  domains: string[];
  license: string;
  status: "active" | "deprecated" | "removed";
  status_reason?: string | null;
  forked_from?: { id: string; version: number } | null;
  details?: { what_you_get?: string; what_it_costs?: string; what_you_need?: string };
  publisher: string;
  tier: "official" | "community";
  latest: number;
  versions: VersionEntry[];
  installs: number;
  /** How it went for people who ran it and said so (registry/tools/outcomes.py). */
  outcomes?: { reports: number; finished: number; median_days: number; median_usd: number | null;
               requirements_met_share: number | null };
}

const files = import.meta.glob("../../public/marketplace/listings/*/*/versions/*.json", { eager: true, import: "default" });

/** A version's whole file: the role or the setup file, needs and blanks. */
export function versionBody(entry: VersionEntry): any {
  const key = `../../public/marketplace/${entry.path}`;
  return files[key];
}

export const listings: Listing[] = [...(index.listings as unknown as Listing[])].sort(
  (a, b) => (a.tier === "official" ? 0 : 1) - (b.tier === "official" ? 0 : 1)
    || (b.installs ?? 0) - (a.installs ?? 0) || a.name.localeCompare(b.name),
);

export const active = listings.filter((l) => l.status !== "removed");

export function latest(listing: Listing): VersionEntry {
  return listing.versions.find((v) => v.version === listing.latest) ?? listing.versions.at(-1)!;
}

export function slugOf(listing: Listing): { handle: string; slug: string } {
  const [handle, slug] = listing.id.slice(1).split("/");
  return { handle, slug };
}

export function hrefOf(listing: Listing): string {
  const { handle, slug } = slugOf(listing);
  return `/marketplace/${handle}/${slug}/`;
}

/** What a role may do, in plain words. Only running commands is marked:
    a warning on everything is a warning nobody reads. */
export const CAN_DO: Record<string, string> = {
  web: "Reads the web",
  files: "Reads and writes files",
  bash: "Runs commands",
};

export function canDo(tools: string[]): string[] {
  return tools.length ? tools.map((t) => CAN_DO[t] ?? t) : ["Replies only"];
}

/** yaaf's install screen for a listing, on an install at `base`. The site
    rewrites `base` from the visitor's saved address. */
export function openInYaaf(listing: Listing, base = "http://localhost:24247"): string {
  const q = new URLSearchParams({ source: INDEX_URL, id: listing.id });
  return `${base}/#/library/install?${q.toString()}`;
}

export function installCommand(listing: Listing): string {
  return `yaaf install ${listing.id}`;
}

export function reportHref(listing: Listing): string {
  const q = new URLSearchParams({ template: "report.yml", listing: listing.id });
  return `${REGISTRY_REPO}/issues/new?${q.toString()}`;
}

export const CATEGORY_WORDS: Record<string, string> = {
  leadership: "Leadership",
  research: "Research",
  build: "Build",
  content: "Content",
  challenge: "Challenge",
  growth: "Growth",
};

export const generatedAt = index.generated_at;
