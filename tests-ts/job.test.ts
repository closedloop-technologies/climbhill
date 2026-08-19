import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, mkdir, readFile, readdir, rename, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";
import { discoverJob, initializeJob, recoverJob } from "../src/job.js";
import { addSource, ArxivAdapter, FileAdapter, PdfAdapter, updateResource, WebpageAdapter, YouTubeAdapter } from "../src/source.js";
import { deriveResource } from "../src/derive.js";
import { buildGraph } from "../src/graph.js";
import { rebuildCache } from "../src/run-store.js";
import { validateOkf } from "../src/okf-validator.js";
import { attachCandidatePatch, compareCandidates, decideCandidate, evaluateCandidate, planImprovement, promoteSkill, recordReflection } from "../src/improvement.js";
import { runResearch } from "../src/research.js";
import { classifyPaths, updateBudgets } from "../src/policy.js";
import { LocatorKind, ObservationKind, type DerivedObservation } from "../src/baml_client/types.js";

const exec = promisify(execFile);

async function git(repo: string, ...args: string[]): Promise<string> {
  return (await exec("git", ["-C", repo, ...args], { encoding: "utf8" })).stdout.trim();
}

async function repository(parent: string, name: string): Promise<string> {
  const path = join(parent, name);
  await mkdir(path);
  await git(path, "init", "-b", "main");
  await git(path, "config", "user.email", "tests@climbhill.ai");
  await git(path, "config", "user.name", "ClimbHill Tests");
  await writeFile(join(path, "README.md"), `# ${name}\n`);
  await git(path, "add", "README.md");
  await git(path, "commit", "-m", "initial");
  return path;
}

test("split-control init preserves branches, refuses ambiguity, and survives worktree moves", async () => {
  const parent = await mkdtemp(join(tmpdir(), "climbhill-split-"));
  const target = await repository(parent, "target");
  const control = await repository(parent, "control");
  const location = join(parent, "worktrees");
  const beforeTarget = await git(target, "branch", "--show-current");
  const beforeControl = await git(control, "branch", "--show-current");
  const initialized = await initializeJob({ target, control, location, job: "source quality", objective: "Improve source quality" });
  assert.equal(await git(target, "branch", "--show-current"), beforeTarget);
  assert.equal(await git(control, "branch", "--show-current"), beforeControl);
  assert.match(initialized.job.id, /^source-quality-[a-f0-9]{12}$/);
  const pointer = await readFile(initialized.pointerPath, "utf8");
  assert.doesNotMatch(pointer, new RegExp(parent.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  await assert.rejects(() => initializeJob({ target, control, location, job: "source quality" }), /already exists/);
  const moved = join(parent, "moved-control-worktree");
  await git(control, "worktree", "move", initialized.controlWorktree, moved);
  const discovered = await discoverJob(target);
  assert.equal(discovered.worktree, moved);
  assert.equal(discovered.job.id, initialized.job.id);
  await rename(initialized.pointerPath, `${initialized.pointerPath}.bak`);
  const recovered = await recoverJob({ target, control, location, jobId: initialized.job.id });
  assert.equal(recovered.controlWorktree, moved);
  assert.equal((await discoverJob(target)).job.id, initialized.job.id);
});

test("Ouroboros init uses a separate branch and worktree", async () => {
  const parent = await mkdtemp(join(tmpdir(), "climbhill-ouroboros-"));
  const repo = await repository(parent, "repo");
  const initialized = await initializeJob({ target: repo, control: repo, location: join(parent, "worktrees"), job: "self improve" });
  assert.equal(await git(repo, "branch", "--show-current"), "main");
  assert.equal(await git(initialized.controlWorktree, "branch", "--show-current"), initialized.job.controlBranch);
  assert.notEqual(repo, initialized.controlWorktree);
});

test("every MVP source adapter creates an addressable OKF resource", async () => {
  const parent = await mkdtemp(join(tmpdir(), "climbhill-adapters-"));
  const repo = await repository(parent, "repo");
  const initialized = await initializeJob({ target: repo, control: repo, location: join(parent, "worktrees"), job: "adapters" });
  const root = join(initialized.controlWorktree, ".climbhill", initialized.job.id);

  const file = join(parent, "notes.txt");
  await writeFile(file, "Local evidence.\n");
  const local = await addSource(root, file, "file", [new FileAdapter()]);

  const pdf = join(parent, "paper.pdf");
  await writeFile(pdf, Buffer.from("%PDF-1.4 deterministic fixture\n"));
  const document = await addSource(root, pdf, "pdf", [new PdfAdapter()]);

  const webpage = await addSource(root, "https://example.test/article", "webpage", [new WebpageAdapter(async () => new Response(
    "<html><head><title>Primary Article</title></head><body>Evidence</body></html>",
    { status: 200, headers: { "content-type": "text/html" } },
  ))]);

  const youtube = await addSource(root, "https://youtu.be/example", "youtube", [new YouTubeAdapter(
    async () => new Response(JSON.stringify({ title: "Expert Talk", author_name: "A. Expert", provider_name: "YouTube" }), { status: 200, headers: { "content-type": "application/json" } }),
    async () => [{ offset: 1250, duration: 3000, text: "Timestamped evidence", lang: "en" }],
  )]);

  const arxivXml = `<?xml version="1.0"?><feed><entry><id>https://arxiv.org/abs/2401.01234v3</id><title>Versioned Paper</title><author><name>A. Researcher</name></author><published>2024-01-03T00:00:00Z</published></entry></feed>`;
  const arxiv = await addSource(root, "https://arxiv.org/abs/2401.01234", "arxiv", [new ArxivAdapter(async (url) => url.includes("api/query")
    ? new Response(arxivXml, { status: 200, headers: { "content-type": "application/atom+xml" } })
    : new Response(Buffer.from("%PDF-1.4 arxiv fixture\n"), { status: 200, headers: { "content-type": "application/pdf" } }))]);

  assert.equal(local.resource.type, "file");
  assert.equal(document.resource.metadata.locator, "page");
  assert.equal(webpage.resource.title, "Primary Article");
  assert.equal(youtube.resource.metadata.locator, "timestamp");
  assert.match(youtube.resource.rawPath, /\.json$/);
  assert.equal(arxiv.resource.metadata.locator, "page");
  assert.equal(arxiv.resource.metadata.arxivId, "2401.01234v3");
  assert.equal(arxiv.resource.source, "https://arxiv.org/abs/2401.01234v3");
  assert.equal((await validateOkf(root)).errors.length, 0);
});

test("source versions, derivations, graph builds, OKF, and cache are idempotent", async () => {
  const parent = await mkdtemp(join(tmpdir(), "climbhill-evidence-"));
  const repo = await repository(parent, "repo");
  const initialized = await initializeJob({ target: repo, control: repo, location: join(parent, "worktrees"), job: "evidence" });
  const root = join(initialized.controlWorktree, ".climbhill", initialized.job.id);
  const source = join(parent, "source.txt");
  await writeFile(source, "Ada Lovelace created an algorithm.\nThe evidence is incomplete.\n");
  const first = await addSource(root, source);
  const resourcePath = join(root, "research", "okf", "resources", `${first.resource.id}.md`);
  await writeFile(resourcePath, (await readFile(resourcePath, "utf8")).replace("version: 1\n", "version: 1\nproducer_extension: preserved\n"));
  await updateResource(root, { ...first.resource, derivationStatus: "succeeded" });
  assert.match(await readFile(resourcePath, "utf8"), /producer_extension: preserved/);
  const duplicate = await addSource(root, source);
  assert.equal(duplicate.duplicate, true);
  assert.equal(duplicate.resource.id, first.resource.id);
  await writeFile(source, "Ada Lovelace created an algorithm.\nThe evidence is now complete.\n");
  const changed = await addSource(root, source);
  assert.equal(changed.resource.version, 2);
  assert.notEqual(changed.resource.contentHash, first.resource.contentHash);

  const fake = {
    async derive(): Promise<DerivedObservation[]> {
      return [
        { kind: ObservationKind.Entity, text: "Ada Lovelace", locator_kind: LocatorKind.Line, locator_value: "1", relationship_subject: null, relationship_type: null, relationship_object: null },
        { kind: ObservationKind.Claim, text: "The evidence is complete.", locator_kind: LocatorKind.Line, locator_value: "2", relationship_subject: null, relationship_type: null, relationship_object: null },
      ];
    },
  };
  const derived = await deriveResource(root, first.resource.id, { client: fake });
  const cached = await deriveResource(root, first.resource.id, { client: { derive: async () => { throw new Error("cache miss"); } } });
  assert.equal(cached.cached, true);
  assert.equal(cached.observations[0].generated.at, derived.observations[0].generated.at);
  await deriveResource(root, changed.resource.id, { client: { async derive() { return [
    { kind: ObservationKind.Entity, text: "Ada Lovelace", locator_kind: LocatorKind.Line, locator_value: "1", relationship_subject: null, relationship_type: null, relationship_object: null },
    { kind: ObservationKind.Claim, text: "The evidence is not complete.", locator_kind: LocatorKind.Line, locator_value: "2", relationship_subject: null, relationship_type: null, relationship_object: null },
  ]; } } });
  const graph = await buildGraph(root);
  const unchanged = await buildGraph(root);
  assert.equal(graph.cached, false);
  assert.equal(unchanged.cached, true);
  assert.ok(graph.summary.concepts.every((concept) => concept.observations.length > 0 && concept.rationale));
  assert.equal(graph.summary.conflicts, 1);
  assert.ok(graph.summary.concepts.find((concept) => concept.conflicts)?.observations.length === 2);
  const validation = await validateOkf(root);
  assert.deepEqual(validation.errors, []);
  const rebuilt = await rebuildCache(root);
  assert.equal(rebuilt.runs, 0);
  assert.ok(rebuilt.concepts >= 5);
});

test("recursive runs preserve lineage, evaluations, decisions, and skill provenance", async () => {
  const parent = await mkdtemp(join(tmpdir(), "climbhill-runs-"));
  const repo = await repository(parent, "repo");
  const initialized = await initializeJob({ target: repo, control: repo, location: join(parent, "worktrees"), job: "recursive" });
  const root = join(initialized.controlWorktree, ".climbhill", initialized.job.id);
  assert.deepEqual(classifyPaths(initialized.job, ["src/app.ts", ".github/workflows/ci.yml", ".env"]).map((value) => value.classification), ["allowed", "approval-required", "denied"]);
  await assert.rejects(() => updateBudgets(root, initialized.job, { maxApiCostUsd: 10 }, "Need more evidence", false), /--approve/);
  const updatedJob = await updateBudgets(root, initialized.job, { maxApiCostUsd: 10 }, "Approved larger research run", true);
  assert.equal(updatedJob.budgets.maxApiCostUsd, 10);
  const source = join(parent, "evidence.txt");
  await writeFile(source, "Use deterministic evaluation commands.\n");
  const resource = (await addSource(root, source)).resource;
  const derived = await deriveResource(root, resource.id, { client: { async derive() { return [{ kind: ObservationKind.Recommendation, text: "Use deterministic evaluation commands.", locator_kind: LocatorKind.Line, locator_value: "1", relationship_subject: null, relationship_type: null, relationship_object: null }]; } } });
  const first = await planImprovement(root, initialized.controlWorktree, repo, { goal: "Improve evaluation", candidates: 1 });
  const child = await planImprovement(root, initialized.controlWorktree, repo, { goal: "Refine evaluation", candidates: 1, parentRun: first.id, parentCandidate: first.candidates[0] });
  assert.equal(child.parentRun, first.id);
  assert.equal(child.parentCandidate, first.candidates[0]);
  const evaluation = await evaluateCandidate(root, repo, child.id, child.candidates[0], "node -e \"process.exit(0)\"", 10);
  assert.equal(evaluation.status, "passed");
  assert.equal((await compareCandidates(root, child.id))[0].passed, 1);
  const patch = join(parent, "candidate.patch");
  await writeFile(patch, "diff --git a/README.md b/README.md\n");
  assert.match(await attachCandidatePatch(root, child.id, child.candidates[0], patch, "deadbeef"), /\.patch$/);
  const reflectionId = await recordReflection(root, child.id, "Deterministic evaluation made the decision reviewable.");
  assert.match(reflectionId, /^reflection-/);
  await assert.rejects(() => decideCandidate(root, child.id, child.candidates[0], "promote", "Passes", false), /--approve/);
  await decideCandidate(root, child.id, child.candidates[0], "promote", "All required checks pass.", true);
  const skill = join(parent, "verified-skill");
  await mkdir(skill);
  await writeFile(join(skill, "SKILL.md"), "---\nname: verified-skill\ndescription: Verified behavior.\n---\n");
  const destination = await promoteSkill(root, repo, initialized.job, { source: skill, concepts: [derived.observations[0].id], runId: child.id, evaluations: [evaluation.id], approved: true });
  assert.match(destination, /\.agent\/skills\/verified-skill$/);
  assert.match(await readFile(join(destination, "SKILL.md"), "utf8"), /Verified behavior/);
  const promotions = await readdir(join(root, "skill-promotions"));
  assert.equal(promotions.length, 1);
  assert.match(await readFile(join(root, "skill-promotions", promotions[0]), "utf8"), new RegExp(derived.observations[0].id));
});

test("research preserves budget-limited state and resumes without repeating searches", async () => {
  const parent = await mkdtemp(join(tmpdir(), "climbhill-research-"));
  const repo = await repository(parent, "repo");
  const initialized = await initializeJob({ target: repo, control: repo, location: join(parent, "worktrees"), job: "research" });
  const root = join(initialized.controlWorktree, ".climbhill", initialized.job.id);
  const client = {
    async plan() { return { existing_evidence_summary: "No local evidence.", missing_evidence: ["Primary source"], searches: ["primary source"], completion_criteria: ["One source"] }; },
    async synthesize() { return { answer: "No source was acquired.", concept_ids: [], remaining_uncertainties: ["Evidence missing"] }; },
  };
  let searches = 0;
  const searchClient = { async search() { searches += 1; return { urls: [], cost: 0.5, raw: {} }; } };
  const partial = await runResearch(root, initialized.controlWorktree, "What is known?", { maxApiCostUsd: 0.5, maxWallTimeSeconds: 30, targetRepository: repo, client, searchClient });
  assert.equal(partial.status, "partial");
  const resumed = await runResearch(root, initialized.controlWorktree, "What is known?", { maxApiCostUsd: 1, maxWallTimeSeconds: 30, targetRepository: repo, client, searchClient, resumeRunId: partial.runId });
  assert.equal(resumed.status, "completed");
  assert.equal(resumed.runId, partial.runId);
  assert.equal(searches, 1);
  assert.match(await readFile(join(root, "runs", partial.runId, "partial.md"), "utf8"), /api-cost-budget-reached/);
  const local = await runResearch(root, initialized.controlWorktree, "Use only local evidence", { localOnly: true, maxApiCostUsd: 1, maxWallTimeSeconds: 30, targetRepository: repo, client, searchClient: { async search() { throw new Error("local-only attempted retrieval"); } } });
  assert.equal(local.status, "completed");
});
