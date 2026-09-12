/**
 * Everything about this site that is a decision rather than content.
 * One file, so a domain change or a launch flip is one edit.
 */

/** Canonical origin. No trailing slash. Change this when the domain is decided. */
export const SITE_URL = "https://yaaf.dev";

/** Set false before the yaaf repo is public: every GitHub CTA becomes a waitlist CTA. */
export const SOURCE_IS_PUBLIC = true;

export const REPO_URL = "https://github.com/dominicplouffe/yaaf";
export const REPO_SLUG = "dominicplouffe/yaaf";
export const LICENSE = "Apache-2.0";
export const LICENSE_URL = `${REPO_URL}/blob/main/LICENSE`;

/** Where "get it" points, depending on the flag above. */
export const PRIMARY_CTA = SOURCE_IS_PUBLIC
  ? { label: "Source on GitHub", href: REPO_URL }
  : { label: "Get notified", href: "#notify" };

export const SITE = {
  name: "yaaf",
  /** Used in <title> and og:site_name. */
  tagline: "Stop prompting. Start delegating.",
  description:
    "yaaf hires a crew of agents — roles, a CEO, a budget and a delivery date — and enforces the rules in the server, where an agent's token cannot reach them. You are the chairman.",
  themeColor: "#0d0d0d",
};

export const NAV = [
  { label: "Why yaaf", href: "/why/" },
  { label: "The org", href: "/org/" },
  { label: "Examples", href: "/examples/" },
  { label: "Docs", href: "/docs/" },
];

/** Docs sidebar order. Anything synced but unlisted is appended under "More". */
export const DOCS_ORDER = [
  "plan",
  "features",
  "creating-a-project",
  "governance",
  "security",
  "autonomy",
  "mcp-server",
  "dashboard",
  "agent-api",
  "integrations",
  "cli",
  "deployment",
  "goal-grammar",
];

export const DOCS_GROUPS = [
  { title: "Start here", slugs: ["plan", "features", "creating-a-project"] },
  { title: "The rules", slugs: ["governance", "autonomy", "security", "goal-grammar"] },
  { title: "Surfaces", slugs: ["mcp-server", "dashboard", "cli", "agent-api"] },
  { title: "Running it", slugs: ["deployment", "integrations"] },
];
