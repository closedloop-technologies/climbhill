import { exec } from "node:child_process";
import { cp, mkdir, readFile, readdir } from "node:fs/promises";
import { basename, join, resolve, sep } from "node:path";
import { promisify } from "node:util";
import { atomicWrite, now, readYaml, shortId, writeYaml } from "./io.js";
import { createRun, updateRun } from "./run-store.js";
import type { JobRecord, RunRecord } from "./types.js";

const execAsync = promisify(exec);

export interface AttemptRecord {
  schema: "climbhill.attempt/v1";
  id: string;
  runId: string;
  status: "planned" | "evaluated" | "rejected" | "promotable";
  branch: string;
  summary: string;
  baseCommit: string;
  headCommit?: string;
  patchPath?: string;
  parentAttempt?: string;
  createdAt: string;
}

export interface EvaluationRecord {
  schema: "climbhill.evaluation/v1";
  id: string;
  runId: string;
  attemptId: string;
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

export async function planImprovement(root: string, worktree: string, targetRepository: string, values: { goal: string; attempts: number; parentRun?: string; parentAttempt?: string }): Promise<RunRecord> {
  if (!Number.isInteger(values.attempts) || values.attempts < 1) throw new Error("--attempts must be a positive integer");
  let run = await createRun(root, worktree, { kind: "improvement", inputs: { goal: values.goal }, parentRun: values.parentRun, parentAttempt: values.parentAttempt }, targetRepository);
  const attemptIds: string[] = [];
  for (let index = 1; index <= values.attempts; index += 1) {
    const id = `attempt-${shortId()}`;
    const attempt: AttemptRecord = { schema: "climbhill.attempt/v1", id, runId: run.id, status: "planned", branch: `climbhill/run-${run.id}/${id}`, summary: `Attempt ${index}: ${values.goal}`, baseCommit: run.targetCommit, ...(values.parentAttempt ? { parentAttempt: values.parentAttempt } : {}), createdAt: now() };
    await writeYaml(join(root, "runs", run.id, "attempts", `${id}.yaml`), attempt);
    attemptIds.push(id);
  }
  await atomicWrite(join(root, "runs", run.id, "plan.md"), `# Plan\n\nGoal: ${values.goal}\n\n${attemptIds.map((id) => `- ${id}`).join("\n")}\n`);
  run = await updateRun(root, run, { attempts: attemptIds });
  return run;
}

export async function evaluateAttempt(root: string, targetRepository: string, runId: string, attemptId: string, command: string, maxWallTimeSeconds: number): Promise<EvaluationRecord> {
  let run = await loadRun(root, runId);
  const attemptPath = join(root, "runs", runId, "attempts", `${attemptId}.yaml`);
  const attempt = await readYaml<AttemptRecord>(attemptPath);
  if (attempt.runId !== runId) throw new Error("attempt does not belong to run");
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
  const evaluation: EvaluationRecord = { schema: "climbhill.evaluation/v1", id, runId, attemptId, command, status: exitCode === 0 ? "passed" : "failed", exitCode, startedAt, completedAt: now(), wallTimeSeconds: (Date.now() - started) / 1000, logsPath: relativeLogs };
  await writeYaml(join(root, "runs", runId, "evaluations", `${id}.yaml`), evaluation);
  attempt.status = exitCode === 0 ? "promotable" : "evaluated";
  await writeYaml(attemptPath, attempt);
  run = await updateRun(root, run, { evaluations: [...run.evaluations, id], costs: { ...run.costs, wallTimeSeconds: run.costs.wallTimeSeconds + evaluation.wallTimeSeconds } });
  return evaluation;
}

export async function compareAttempts(root: string, runId: string): Promise<Array<{ attempt: AttemptRecord; passed: number; failed: number }>> {
  const run = await loadRun(root, runId);
  const evaluations = await Promise.all((await readdir(join(root, "runs", runId, "evaluations"))).filter((name) => name.endsWith(".yaml")).map((name) => readYaml<EvaluationRecord>(join(root, "runs", runId, "evaluations", name))));
  const rows = await Promise.all(run.attempts.map(async (id) => {
    const attempt = await readYaml<AttemptRecord>(join(root, "runs", runId, "attempts", `${id}.yaml`));
    const own = evaluations.filter((value) => value.attemptId === id);
    return { attempt, passed: own.filter((value) => value.status === "passed").length, failed: own.filter((value) => value.status === "failed").length };
  }));
  return rows.sort((a, b) => b.passed - a.passed || a.failed - b.failed || a.attempt.id.localeCompare(b.attempt.id));
}

export async function attachAttemptPatch(root: string, runId: string, attemptId: string, patchFile: string, headCommit?: string): Promise<string> {
  const attemptPath = join(root, "runs", runId, "attempts", `${attemptId}.yaml`);
  const attempt = await readYaml<AttemptRecord>(attemptPath);
  if (attempt.runId !== runId) throw new Error("attempt does not belong to run");
  const patch = await readFile(resolve(patchFile));
  const relative = `attempts/${attemptId}.patch`;
  await atomicWrite(join(root, "runs", runId, relative), patch);
  attempt.patchPath = relative;
  if (headCommit) attempt.headCommit = headCommit;
  await writeYaml(attemptPath, attempt);
  return relative;
}

export async function recordReflection(root: string, runId: string, text: string): Promise<string> {
  let run = await loadRun(root, runId);
  const id = `reflection-${shortId()}`;
  await atomicWrite(join(root, "runs", runId, "reflection.md"), `# Reflection\n\n- ID: ${id}\n\n${text}\n`);
  run = await updateRun(root, run, { reflections: [...run.reflections, id] });
  return id;
}

export async function decideAttempt(root: string, runId: string, attemptId: string, decision: "promote" | "reject", rationale: string, approved: boolean): Promise<void> {
  let run = await loadRun(root, runId);
  const job = await readYaml<JobRecord>(join(root, "job.yaml"));
  if (decision === "promote" && !approved) throw new Error("promotion requires explicit --approve");
  const attemptPath = join(root, "runs", runId, "attempts", `${attemptId}.yaml`);
  const attempt = await readYaml<AttemptRecord>(attemptPath);
  const evaluations = await Promise.all(run.evaluations.map((id) => readYaml<EvaluationRecord>(join(root, "runs", runId, "evaluations", `${id}.yaml`))));
  const own = evaluations.filter((value) => value.attemptId === attemptId);
  if (decision === "promote" && (!own.length || own.some((value) => value.status !== "passed"))) throw new Error("promotion requires at least one evaluation and no failed evaluations");
  if (decision === "promote") {
    const missing = job.policy.requiredEvaluations.filter((requiredCommand) => !own.some((value) => value.status === "passed" && value.command === requiredCommand));
    if (missing.length) throw new Error(`required evaluations have not passed: ${missing.join(", ")}`);
  }
  attempt.status = decision === "promote" ? "promotable" : "rejected";
  await writeYaml(attemptPath, attempt);
  const decisionId = `decision-${shortId()}`;
  await atomicWrite(join(root, "runs", runId, "decision.md"), `# Decision\n\n- ID: ${decisionId}\n- Attempt: ${attemptId}\n- Decision: ${decision}\n- Human approved: ${approved}\n\n${rationale}\n`);
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
