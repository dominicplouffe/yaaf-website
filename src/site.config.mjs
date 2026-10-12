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
  tagline: "Hire an AI team. Get the project done.",
  description:
    "Describe a project in plain English. yaaf builds a team of AI agents, manages them for days or weeks and checks every result. Free and open source.",
  themeColor: "#000000",
};

export const NAV = [
  { label: "How it works", href: "/how-it-works/" },
  { label: "Use cases", href: "/examples/" },
  { label: "Features", href: "/features/" },
  { label: "The team", href: "/org/" },
  { label: "Compare", href: "/compare/" },
  { label: "Docs", href: "/docs/" },
];

/** Pages that are reference rather than navigation; the footer lists them. */
export const MORE = [
  { label: "Supported models", href: "/runtimes/" },
  { label: "FAQ", href: "/faq/" },
  { label: "What's new", href: "/changelog/" },
  { label: "Security model", href: "/docs/security/" },
  { label: "The plan", href: "/docs/plan/" },
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
  "runtimes",
  "auth",
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
  { title: "Running it", slugs: ["deployment", "integrations", "runtimes", "auth"] },
];
