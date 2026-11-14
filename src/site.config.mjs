/**
 * Everything about this site that is a decision rather than content.
 * One file, so a domain change or a launch flip is one edit.
 */

/** Canonical origin. No trailing slash. Must match SITE_HOST in the deploy settings. */
export const SITE_URL = "https://yaaf.dplouffe.ca";

/**
 * Off for now: the comparison with other tools (the Compare page, its nav
 * item, the home page's "Why not just use Claude Code?" and the FAQ's
 * Paperclip answer). To bring it back, set this true and rename
 * src/pages/_compare.astro to compare.astro (Astro skips files that start
 * with an underscore), then point the /why redirect in astro.config.mjs back
 * at /compare/.
 */
export const SHOW_COMPARE = false;

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
  /** The brand's primary tagline. Used in the home page's <title> and the footer. */
  tagline: "Rules agents can't talk their way out of.",
  /** The messaging kit's short description (160 characters or fewer). */
  description:
    "yaaf runs a team of AI agents like a company you chair. The rules live in the server, not the prompt. Open source, on your machine.",
  /** Registry paper and Carbon: the browser chrome follows the page in each scheme. */
  themeColor: { light: "#F4F4F1", dark: "#121316" },
};

const NAV_ALL = [
  { label: "How it works", href: "/how-it-works/" },
  { label: "Manifesto", href: "/manifesto/" },
  { label: "Harnesses", href: "/runtimes/" },
  { label: "Features", href: "/features/" },
  { label: "The team", href: "/org/" },
  { label: "Compare", href: "/compare/" },
  { label: "Docs", href: "/docs/" },
];
export const NAV = NAV_ALL.filter((i) => SHOW_COMPARE || i.href !== "/compare/");

/** Pages that are reference rather than navigation; the footer lists them. */
export const MORE = [
  { label: "FAQ", href: "/faq/" },
  { label: "What's new", href: "/changelog/" },
  { label: "Security model", href: "/docs/security/" },
];

/** Docs sidebar order. Anything synced but unlisted is appended under "More". */
export const DOCS_ORDER = [
  "install",
  "configuration",
  "deployment",
  "architecture",
  "providers",
  "cli",
  "security",
];

export const DOCS_GROUPS = [
  { title: "Get it running", slugs: ["install", "configuration", "deployment"] },
  { title: "How it works", slugs: ["architecture", "providers", "security"] },
  { title: "Reference", slugs: ["cli"] },
];
