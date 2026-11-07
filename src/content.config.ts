import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

/** A job description in yaaf's role library. Mirrors roles/*.json exactly. */
const roles = defineCollection({
  loader: glob({ pattern: "*.json", base: "./src/content/roles" }),
  schema: z.object({
    slug: z.string(),
    name: z.string(),
    is_ceo_role: z.boolean(),
    category: z.enum(["research", "challenge", "content", "growth", "build", "leadership"]),
    domains: z.array(z.string()),
    description: z.string(),
    // Gone from roles since yaaf#79: the app picks the model and harness.
    model: z.string().optional(),
    effort: z.string(),
    tool_permissions: z.record(z.string(), z.boolean()).default({}),
    secret_scopes: z.array(z.string()).default([]),
    system_prompt: z.string(),
  }),
});

/** A pre-built org: teams, the roles filling them, and who leads. */
const crews = defineCollection({
  loader: glob({ pattern: "*.json", base: "./src/content/crews" }),
  schema: z.object({
    slug: z.string(),
    name: z.string(),
    outcome: z.string(),
    ceo_role_slug: z.string(),
    domains: z.array(z.string()),
    source: z.string(),
    teams: z.array(
      z.object({
        name: z.string(),
        role_slug: z.string(),
        // A crew may be a single seat: no named employees, no lead.
        employees: z.array(z.string()).default([]),
        lead: z.string().optional(),
        schedules: z.any().optional(),
      }),
    ),
  }),
});

const docs = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/docs" }),
  schema: z.object({
    title: z.string(),
    subtitle: z.string(),
    slug: z.string(),
    sourceFile: z.string(),
  }),
});

export const collections = { roles, crews, docs };
