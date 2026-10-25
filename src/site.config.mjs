/**
 * Everything about this site that is a decision rather than content.
 * One file, so a domain change or a launch flip is one edit.
 */

/** Canonical origin. No trailing slash. Must match SITE_HOST in the deploy settings. */
export const SITE_URL = "https://yaaf.dplouffe.ca";

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
  tagline: "Build a company. Hire a CEO. Let the team work.",
  description:
    "yaaf is the open-source harness for teams of harnesses. Build a company of AI agents — a CEO, teams on Claude Code, Codex, Gemini CLI or any model — and chair it from your own machine, with work the platform verifies, money that stops itself and a date nobody can quietly move.",
  themeColor: "#0b0918",
};

export const NAV = [
  { label: "How it works", href: "/how-it-works/" },
  { label: "Harnesses", href: "/runtimes/" },
  { label: "Use cases", href: "/examples/" },
  { label: "Features", href: "/features/" },
  { label: "The team", href: "/org/" },
  { label: "Compare", href: "/compare/" },
  { label: "Docs", href: "/docs/" },
];

/** Pages that are reference rather than navigation; the footer lists them. */
export const MORE = [
  { label: "FAQ", href: "/faq/" },
  { label: "What's new", href: "/changelog/" },
  { label: "Security model", href: "/docs/security/" },
];

/** Docs sidebar order. Anything synced but unlisted is appended under "More". */
export const DOCS_ORDER = [
  "features",
  "creating-a-project",
  "governance",
  "security",
  "autonomy",
  "mcp-server",
  "runtimes",
  "providers",
  "auth",
  "dashboard",
  "agent-api",
  "integrations",
  "cli",
  "deployment",
  "goal-grammar",
];

export const DOCS_GROUPS = [
  { title: "Start here", slugs: ["features", "creating-a-project"] },
  { title: "The rules", slugs: ["governance", "autonomy", "security", "goal-grammar"] },
  { title: "Surfaces", slugs: ["mcp-server", "dashboard", "cli", "agent-api"] },
  { title: "Running it", slugs: ["deployment", "integrations", "runtimes", "providers", "auth"] },
];
