import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { b } from "./baml_client/async_client.js";
import type { DerivedObservation } from "./baml_client/types.js";
import { atomicWrite, frontmatter, hash, now, parseFrontmatter, readYaml, writeYaml } from "./io.js";
import { extractText } from "./source.js";
import type { Observation, ResourceVersion } from "./types.js";
import { Collector } from "@boundaryml/baml";
import { OPENAI_MODEL, type TokenUsage } from "./model-cost.js";

export const DEFAULT_DERIVATION_PROMPT = "Apply Bloom's revised cognitive lenses and extract source-local evidence only.";
export const DERIVATION_PROFILE = "bloom-revised/v1";
export const DERIVATION_SCHEMA = "climbhill.observation/v1";
export const CHUNKING_POLICY = "whole-document/v1";
export const DEFAULT_MODEL = OPENAI_MODEL;

export interface DerivationClient {
  derive(content: string, resourceId: string, locatorGuidance: string, resolvedPrompt: string): Promise<DerivedObservation[]>;
}

export async function loadResource(root: string, id: string): Promise<ResourceVersion> {
  const content = await readFile(join(root, "research", "okf", "resources", `${id}.md`), "utf8");
  return parseFrontmatter<ResourceVersion>(content).data;
}

export async function deriveResource(root: string, resourceId: string, options: {
  appendPrompt?: string;
  promptFile?: string;
  model?: string;
  client?: DerivationClient;
} = {}): Promise<{ identity: string; observations: Observation[]; cached: boolean; usage?: TokenUsage }> {
  const resource = await loadResource(root, resourceId);
  const custom = options.promptFile ? await readFile(options.promptFile, "utf8") : undefined;
  const resolvedPrompt = custom || `${DEFAULT_DERIVATION_PROMPT}${options.appendPrompt ? `\n\n${options.appendPrompt}` : ""}`;
  const model = options.model || DEFAULT_MODEL;
  const identity = hash(JSON.stringify({ raw: resource.contentHash, profile: DERIVATION_PROFILE, prompt: resolvedPrompt, model, schema: DERIVATION_SCHEMA, chunking: CHUNKING_POLICY }));
  const directory = join(root, "research", "okf", "observations");
  const prefix = `${resource.id}-${identity.slice(0, 16)}-`;
  const existing = (await readdir(directory)).filter((name) => name.startsWith(prefix) && name.endsWith(".md"));
  const manifestPath = join(directory, `${resource.id}-${identity.slice(0, 16)}-derivation.yaml`);
  const manifest = await readYaml<{ observations: string[] }>(manifestPath).catch(() => undefined);
  if (existing.length && manifest?.observations.length === existing.length && manifest.observations.every((id) => existing.includes(`${id}.md`))) {
    const observations = await Promise.all(existing.sort().map(async (name) => parseFrontmatter<Observation>(await readFile(join(directory, name), "utf8")).data));
    return { identity, observations, cached: true };
  }

  const content = await extractText(root, resource);
  const locatorGuidance = resource.type === "youtube" ? "timestamps" : resource.type === "pdf" || resource.type === "arxiv" ? "page numbers" : "line numbers or headings";
  const generatedAt = now();
  let derived: DerivedObservation[];
  let usage: TokenUsage | undefined;
  if (options.client) derived = await options.client.derive(content, resource.id, locatorGuidance, resolvedPrompt);
  else {
    const collector = new Collector("climbhill-derive");
    derived = (await b.DeriveSource(content, resource.id, locatorGuidance, resolvedPrompt, { collector })).observations;
    usage = { inputTokens: collector.usage.inputTokens || 0, outputTokens: collector.usage.outputTokens || 0, cachedInputTokens: collector.usage.cachedInputTokens || 0 };
  }
  if (!derived.length) throw new Error("derivation returned no observations");
  const allowedKinds = new Set(["entity", "fact", "claim", "procedure", "relationship", "recommendation", "gap"]);
  const allowedLocators = new Set(["line", "page", "timestamp", "heading"]);
  const observations: Observation[] = derived.map((value, index) => {
    const type = value.kind.toLowerCase();
    const locatorKind = value.locator_kind.toLowerCase();
    if (!value.text.trim() || !value.locator_value.trim() || !allowedKinds.has(type) || !allowedLocators.has(locatorKind)) throw new Error(`invalid structured observation at index ${index}`);
    return {
      id: `${resource.id}-${identity.slice(0, 16)}-${String(index + 1).padStart(4, "0")}`,
      type: type as Observation["type"], text: value.text.trim(), resourceId: resource.id,
      locator: { kind: locatorKind as Observation["locator"]["kind"], value: value.locator_value.trim() },
      ...(type === "relationship" && value.relationship_subject && value.relationship_type && value.relationship_object ? { relationship: { subject: value.relationship_subject.trim(), type: value.relationship_type.trim(), object: value.relationship_object.trim() } } : {}),
      generated: { at: generatedAt, identity, profile: DERIVATION_PROFILE, model, schema: DERIVATION_SCHEMA, promptHash: hash(resolvedPrompt), chunkingPolicy: CHUNKING_POLICY, verified: false },
    };
  });
  if (observations.some((value) => value.type === "relationship" && !value.relationship)) throw new Error("relationship observations require structured subject, type, and object");
  for (const observation of observations) {
    await atomicWrite(join(directory, `${observation.id}.md`), frontmatter(observation as unknown as Record<string, unknown>, `# ${observation.type}\n\n${observation.text}\n`));
  }
  await writeYaml(manifestPath, { schema: "climbhill.derivation/v1", identity, resourceId: resource.id, rawContentHash: resource.contentHash, profile: DERIVATION_PROFILE, resolvedPrompt, promptHash: hash(resolvedPrompt), model, observationSchema: DERIVATION_SCHEMA, chunkingPolicy: CHUNKING_POLICY, generatedAt, verified: false, observations: observations.map((value) => value.id) });
  return { identity, observations, cached: false, ...(usage ? { usage } : {}) };
}

export async function derivePending(root: string, options: Parameters<typeof deriveResource>[2] = {}): Promise<Array<{ resourceId: string; count: number; cached: boolean; usage?: TokenUsage }>> {
  const resources = await readdir(join(root, "research", "okf", "resources"));
  const results = [];
  for (const name of resources.filter((value) => value.endsWith(".md")).sort()) {
    const id = name.slice(0, -3);
    const result = await deriveResource(root, id, options);
    results.push({ resourceId: id, count: result.observations.length, cached: result.cached, ...(result.usage ? { usage: result.usage } : {}) });
  }
  return results;
}
