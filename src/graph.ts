import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { hash, parseFrontmatter, readYaml, writeConcept, writeYaml } from "./io.js";
import type { Observation } from "./types.js";

interface GraphSummary {
  schema: "climbhill.graph/v1";
  inputHash: string;
  created: number;
  merged: number;
  unresolved: number;
  superseded: number;
  conflicts: number;
  ontology: { entityTypes: string[]; relationshipTypes: string[] };
  concepts: Array<{ id: string; kind: string; observations: string[]; rationale: string; conflicts?: string[] }>;
}

function canonical(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function claimKey(value: string): string {
  return canonical(value).replace(/\b(no|not|never|without|do|does|did)\b/g, "").replace(/\s+/g, " ").trim();
}

export async function buildGraph(root: string): Promise<{ summary: GraphSummary; cached: boolean }> {
  const directory = join(root, "research", "okf", "observations");
  const observations = await Promise.all((await readdir(directory)).filter((name) => name.endsWith(".md")).sort().map(async (name) => parseFrontmatter<Observation>(await readFile(join(directory, name), "utf8")).data));
  const inputHash = hash(JSON.stringify(observations.map((value) => [value.id, value.text, value.resourceId, value.locator])));
  const summaryPath = join(root, "research", "okf", "graph-summary.yaml");
  try {
    const prior = await readYaml<GraphSummary>(summaryPath);
    if (prior.inputHash === inputHash) return { summary: prior, cached: true };
  } catch { /* first build */ }

  const groups = new Map<string, Observation[]>();
  for (const observation of observations.filter((value) => value.type === "entity" || value.type === "claim" || value.type === "relationship")) {
    const key = observation.type === "claim" ? `claim:${claimKey(observation.text)}` : observation.type === "relationship" && observation.relationship ? `relationship:${canonical(observation.relationship.subject)}:${canonical(observation.relationship.type)}:${canonical(observation.relationship.object)}` : `${observation.type}:${canonical(observation.text)}`;
    groups.set(key, [...(groups.get(key) || []), observation]);
  }
  const concepts: GraphSummary["concepts"] = [];
  for (const [key, members] of [...groups.entries()].sort(([a], [b]) => a.localeCompare(b))) {
    const kind = members[0].type;
    const id = `${kind}-${hash(key).slice(0, 16)}`;
    const polarities = new Set(members.map((value) => /\b(no|not|never|without)\b/i.test(value.text) ? "negative" : "positive"));
    const conflicts = kind === "claim" && polarities.size > 1 ? members.map((value) => value.id) : undefined;
    const rationale = conflicts ? "Reconciled under one claim key while retaining contradictory positive and negative observations." : members.length > 1 ? "Merged because normalized source-local meaning and endpoints are identical." : "Kept as a distinct canonical concept; no equivalent normalized observation was found.";
    const body = `# ${members[0].text}\n\n## Resolution\n\n${rationale}\n\n## Evidence\n\n${members.map((value) => `- ${value.id} (${value.resourceId}, ${value.locator.kind}: ${value.locator.value})`).join("\n")}${conflicts ? `\n\n## Conflict\n\nThese observations conflict and remain independently traceable: ${conflicts.join(", ")}.` : ""}`;
    const concept = { id, kind, observations: members.map((value) => value.id), rationale, ...(conflicts ? { conflicts } : {}) };
    concepts.push(concept);
    const target = kind === "entity" ? "entities" : kind === "claim" ? "claims" : "relationships";
    await writeConcept(join(root, "research", "okf", target, `${id}.md`), { type: kind, id, observations: concept.observations, ...(members[0].relationship ? { subject: canonical(members[0].relationship.subject), relationship_type: canonical(members[0].relationship.type), object: canonical(members[0].relationship.object) } : {}), resolution: { rationale, confidence: conflicts ? 0.4 : members.length > 1 ? 0.95 : 0.6, unresolved: members.length === 1, conflicts: conflicts || [] } }, body);
  }
  const summary: GraphSummary = { schema: "climbhill.graph/v1", inputHash, created: concepts.length, merged: [...groups.values()].filter((value) => value.length > 1).length, unresolved: [...groups.values()].filter((value) => value.length === 1).length, superseded: 0, conflicts: concepts.filter((value) => value.conflicts?.length).length, ontology: { entityTypes: ["entity"], relationshipTypes: [...new Set(observations.flatMap((value) => value.relationship ? [canonical(value.relationship.type)] : []))].sort() }, concepts };
  await writeYaml(summaryPath, summary);
  return { summary, cached: false };
}

export async function inspectGraph(root: string): Promise<GraphSummary> {
  return readYaml<GraphSummary>(join(root, "research", "okf", "graph-summary.yaml"));
}
