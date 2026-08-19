const { execFile } = require("node:child_process");
const { mkdtemp, mkdir, writeFile } = require("node:fs/promises");
const { tmpdir } = require("node:os");
const { join, resolve } = require("node:path");
const { promisify } = require("node:util");
const { initializeJob } = require("../dist/npm/job.js");
const { addSource } = require("../dist/npm/source.js");
const { deriveResource } = require("../dist/npm/derive.js");
const { buildGraph } = require("../dist/npm/graph.js");
const { runResearch } = require("../dist/npm/research.js");
const { validateOkf } = require("../dist/npm/okf-validator.js");

const run = promisify(execFile);
(async () => {
const temporary = await mkdtemp(join(tmpdir(), "climbhill-dogfood-"));
const repository = join(temporary, "climbhill");
await run("git", ["clone", "--quiet", resolve(__dirname, ".."), repository]);
await run("git", ["-C", repository, "config", "user.email", "dogfood@climbhill.ai"]);
await run("git", ["-C", repository, "config", "user.name", "ClimbHill Dogfood"]);
const initialized = await initializeJob({ target: repository, control: repository, location: join(temporary, "control"), job: "sota-deep-research-agent", objective: "Improve ClimbHill's deep research agent" });
const root = join(initialized.controlWorktree, ".climbhill", initialized.job.id);
const resource = (await addSource(root, join(repository, "PRD.md"), "file")).resource;
const derivation = await deriveResource(root, resource.id, { client: { async derive() { return [
  { kind: "Entity", text: "ClimbHill", locator_kind: "Heading", locator_value: "1. Executive Summary", relationship_subject: null, relationship_type: null, relationship_object: null },
  { kind: "Claim", text: "ClimbHill is local first.", locator_kind: "Heading", locator_value: "4. Product Principles", relationship_subject: null, relationship_type: null, relationship_object: null },
]; } } });
const graph = await buildGraph(root);
const research = await runResearch(root, initialized.controlWorktree, "What principle governs ClimbHill persistence?", { localOnly: true, maxApiCostUsd: 1, maxWallTimeSeconds: 30, targetRepository: repository, client: {
  async plan() { return { existing_evidence_summary: "The PRD is present locally.", missing_evidence: [], searches: [], completion_criteria: ["Cite a local concept"] }; },
  async synthesize() { return { answer: "ClimbHill is local first and keeps canonical state in version-controlled files.", concept_ids: [derivation.observations[1].id], remaining_uncertainties: [] }; },
} });
const validation = await validateOkf(root);
if (research.status !== "completed" || validation.errors.length) throw new Error(`dogfood failed: ${JSON.stringify({ research, validation })}`);
console.log(JSON.stringify({ jobId: initialized.job.id, mode: "ouroboros", source: resource.id, observations: derivation.observations.length, graphConcepts: graph.summary.created, researchStatus: research.status, okfConcepts: validation.concepts }, null, 2));
})().catch((error) => { console.error(error); process.exitCode = 1; });
