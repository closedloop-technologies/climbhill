import { exec } from "node:child_process";
import { cp, mkdir, readFile, readdir } from "node:fs/promises";
import { basename, join, resolve, sep } from "node:path";
import { promisify } from "node:util";
import { atomicWrite, now, readYaml, shortId, writeYaml } from "./io.js";
import { createRun, updateRun } from "./run-store.js";
import type { JobRecord, RunRecord } from "./types.js";

const execAsync = promisify(exec);

export interface CandidateRecord {
  schema: "climbhill.candidate/v1";
  id: string;
  runId: string;
  status: "planned" | "evaluated" | "rejected" | "promotable";
  branch: string;
  summary: string;
  baseCommit: string;
  headCommit?: string;
  patchPath?: string;
  parentCandidate?: string;
  createdAt: string;
}

export interface EvaluationRecord {
  schema: "climbhill.evaluation/v1";
  id: string;
  runId: string;
  candidateId: string;
  command: string;
  status: "passed" | "failed";
  exitCode: number;
  startedAt: string;
  completedAt: string;
  wallTimeSeconds: number;
  logsPath: string;
}

export async function loadRun(root: string, id: string): Promise<RunRecord> {
  return readYaml<RunRecord>(join(root, "runs", id, "run.yaml"));
}

export async function planImprovement(root: string, worktree: string, targetRepository: string, values: { goal: string; candidates: number; parentRun?: string; parentCandidate?: string }): Promise<RunRecord> {
  if (!Number.isInteger(values.candidates) || values.candidates < 1) throw new Error("--candidates must be a positive integer");
  let run = await createRun(root, worktree, { kind: "improvement", inputs: { goal: values.goal }, parentRun: values.parentRun, parentCandidate: values.parentCandidate }, targetRepository);
  const candidateIds: string[] = [];
  for (let index = 1; index <= values.candidates; index += 1) {
    const id = `candidate-${shortId()}`;
    const candidate: CandidateRecord = { schema: "climbhill.candidate/v1", id, runId: run.id, status: "planned", branch: `climbhill/run-${run.id}/${id}`, summary: `Candidate ${index}: ${values.goal}`, baseCommit: run.targetCommit, ...(values.parentCandidate ? { parentCandidate: values.parentCandidate } : {}), createdAt: now() };
    await writeYaml(join(root, "runs", run.id, "candidates", `${id}.yaml`), candidate);
    candidateIds.push(id);
  }
  await atomicWrite(join(root, "runs", run.id, "plan.md"), `# Plan\n\nGoal: ${values.goal}\n\n${candidateIds.map((id) => `- ${id}`).join("\n")}\n`);
  run = await updateRun(root, run, { candidates: candidateIds });
  return run;
}

export async function evaluateCandidate(root: string, targetRepository: string, runId: string, candidateId: string, command: string, maxWallTimeSeconds: number): Promise<EvaluationRecord> {
  let run = await loadRun(root, runId);
  const candidatePath = join(root, "runs", runId, "candidates", `${candidateId}.yaml`);
  const candidate = await readYaml<CandidateRecord>(candidatePath);
  if (candidate.runId !== runId) throw new Error("candidate does not belong to run");
  const startedAt = now();
  const started = Date.now();
  let stdout = ""; let stderr = ""; let exitCode = 0;
  try {
    const result = await execAsync(command, { cwd: targetRepository, timeout: maxWallTimeSeconds * 1000, maxBuffer: 10 * 1024 * 1024 });
    stdout = result.stdout; stderr = result.stderr;
  } catch (error) {
    const value = error as Error & { stdout?: string; stderr?: string; code?: number | string; killed?: boolean };
    stdout = value.stdout || ""; stderr = value.stderr || value.message; exitCode = typeof value.code === "number" ? value.code : value.killed ? 124 : 1;
  }
  const id = `evaluation-${shortId()}`;
  const relativeLogs = `evaluations/${id}.log`;
  await atomicWrite(join(root, "runs", runId, relativeLogs), `$ ${command}\n\n${stdout}${stderr ? `\n[stderr]\n${stderr}` : ""}\n`);
  const evaluation: EvaluationRecord = { schema: "climbhill.evaluation/v1", id, runId, candidateId, command, status: exitCode === 0 ? "passed" : "failed", exitCode, startedAt, completedAt: now(), wallTimeSeconds: (Date.now() - started) / 1000, logsPath: relativeLogs };
  await writeYaml(join(root, "runs", runId, "evaluations", `${id}.yaml`), evaluation);
  candidate.status = exitCode === 0 ? "promotable" : "evaluated";
  await writeYaml(candidatePath, candidate);
  run = await updateRun(root, run, { evaluations: [...run.evaluations, id], costs: { ...run.costs, wallTimeSeconds: run.costs.wallTimeSeconds + evaluation.wallTimeSeconds } });
  return evaluation;
}

export async function compareCandidates(root: string, runId: string): Promise<Array<{ candidate: CandidateRecord; passed: number; failed: number }>> {
  const run = await loadRun(root, runId);
  const evaluations = await Promise.all((await readdir(join(root, "runs", runId, "evaluations"))).filter((name) => name.endsWith(".yaml")).map((name) => readYaml<EvaluationRecord>(join(root, "runs", runId, "evaluations", name))));
  const rows = await Promise.all(run.candidates.map(async (id) => {
    const candidate = await readYaml<CandidateRecord>(join(root, "runs", runId, "candidates", `${id}.yaml`));
    const own = evaluations.filter((value) => value.candidateId === id);
    return { candidate, passed: own.filter((value) => value.status === "passed").length, failed: own.filter((value) => value.status === "failed").length };
  }));
  return rows.sort((a, b) => b.passed - a.passed || a.failed - b.failed || a.candidate.id.localeCompare(b.candidate.id));
}

export async function attachCandidatePatch(root: string, runId: string, candidateId: string, patchFile: string, headCommit?: string): Promise<string> {
  const candidatePath = join(root, "runs", runId, "candidates", `${candidateId}.yaml`);
  const candidate = await readYaml<CandidateRecord>(candidatePath);
  if (candidate.runId !== runId) throw new Error("candidate does not belong to run");
  const patch = await readFile(resolve(patchFile));
  const relative = `candidates/${candidateId}.patch`;
  await atomicWrite(join(root, "runs", runId, relative), patch);
  candidate.patchPath = relative;
  if (headCommit) candidate.headCommit = headCommit;
  await writeYaml(candidatePath, candidate);
  return relative;
}

export async function recordReflection(root: string, runId: string, text: string): Promise<string> {
  let run = await loadRun(root, runId);
  const id = `reflection-${shortId()}`;
  await atomicWrite(join(root, "runs", runId, "reflection.md"), `# Reflection\n\n- ID: ${id}\n\n${text}\n`);
  run = await updateRun(root, run, { reflections: [...run.reflections, id] });
  return id;
}

export async function decideCandidate(root: string, runId: string, candidateId: string, decision: "promote" | "reject", rationale: string, approved: boolean): Promise<void> {
  let run = await loadRun(root, runId);
  const job = await readYaml<JobRecord>(join(root, "job.yaml"));
  if (decision === "promote" && !approved) throw new Error("promotion requires explicit --approve");
  const candidatePath = join(root, "runs", runId, "candidates", `${candidateId}.yaml`);
  const candidate = await readYaml<CandidateRecord>(candidatePath);
  const evaluations = await Promise.all(run.evaluations.map((id) => readYaml<EvaluationRecord>(join(root, "runs", runId, "evaluations", `${id}.yaml`))));
  const own = evaluations.filter((value) => value.candidateId === candidateId);
  if (decision === "promote" && (!own.length || own.some((value) => value.status !== "passed"))) throw new Error("promotion requires at least one evaluation and no failed evaluations");
  if (decision === "promote") {
    const missing = job.policy.requiredEvaluations.filter((requiredCommand) => !own.some((value) => value.status === "passed" && value.command === requiredCommand));
    if (missing.length) throw new Error(`required evaluations have not passed: ${missing.join(", ")}`);
  }
  candidate.status = decision === "promote" ? "promotable" : "rejected";
  await writeYaml(candidatePath, candidate);
  const decisionId = `decision-${shortId()}`;
  await atomicWrite(join(root, "runs", runId, "decision.md"), `# Decision\n\n- ID: ${decisionId}\n- Candidate: ${candidateId}\n- Decision: ${decision}\n- Human approved: ${approved}\n\n${rationale}\n`);
  run = await updateRun(root, run, { status: decision === "promote" ? "completed" : "rejected", completedAt: now(), stoppingReason: decision, decisions: [...run.decisions, decisionId] });
}

export async function promoteSkill(root: string, targetRepository: string, job: JobRecord, values: { source: string; name?: string; concepts: string[]; runId: string; evaluations: string[]; approved: boolean }): Promise<string> {
  if (!values.approved) throw new Error("skill promotion requires explicit --approve");
  if (!values.concepts.length || !values.evaluations.length) throw new Error("skill promotion requires --concept and --evaluation provenance");
  const source = resolve(values.source);
  await readFile(join(source, "SKILL.md"), "utf8");
  const name = values.name || basename(source);
  if (!/^[a-z0-9][a-z0-9-]*$/.test(name)) throw new Error("skill name must be a lowercase slug");
  const targetRoot = resolve(targetRepository);
  const destination = resolve(targetRoot, ".agent", "skills", name);
  if (!destination.startsWith(`${targetRoot}${sep}`)) throw new Error("skill destination escapes the target repository");
  for (const concept of values.concepts) {
    let found = false;
    for (const directory of ["resources", "observations", "entities", "claims", "relationships", "topics", "reports"]) {
      try { await readFile(join(root, "research", "okf", directory, `${concept}.md`)); found = true; break; } catch { /* try the next concept type */ }
    }
    if (!found) throw new Error(`unknown OKF concept: ${concept}`);
  }
  const run = await loadRun(root, values.runId);
  for (const id of values.evaluations) {
    const evaluation = await readYaml<EvaluationRecord>(join(root, "runs", run.id, "evaluations", `${id}.yaml`));
    if (evaluation.status !== "passed") throw new Error(`evaluation ${id} did not pass`);
  }
  await mkdir(join(targetRoot, ".agent", "skills"), { recursive: true });
  await cp(source, destination, { recursive: true, errorOnExist: true, force: false });
  const promotionId = `skill-${name}-${shortId()}`;
  await writeYaml(join(root, "skill-promotions", `${promotionId}.yaml`), { schema: "climbhill.skill-promotion/v1", id: promotionId, skill: name, targetPath: `.agent/skills/${name}`, jobId: job.id, okfConcepts: values.concepts, runId: values.runId, evaluations: values.evaluations, humanApproved: true, promotedAt: now() });
  return destination;
}
