import { mkdir, readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { atomicWrite, now, readYaml, shortId, writeYaml } from "./io.js";
import { git } from "./git.js";
import { RUN_SCHEMA, type RunRecord } from "./types.js";

export async function createRun(root: string, worktree: string, values: {
  kind: RunRecord["kind"];
  inputs: Record<string, unknown>;
  parentRun?: string;
  parentAttempt?: string;
}, targetRepository = worktree): Promise<RunRecord> {
  const stamp = now();
  const id = `${stamp.slice(0, 10).replaceAll("-", "")}-${values.kind}-${shortId()}`;
  const commit = await git(worktree, ["rev-parse", "HEAD"]);
  const targetCommit = await git(targetRepository, ["rev-parse", "HEAD"]);
  const run: RunRecord = {
    schema: RUN_SCHEMA, id, kind: values.kind, status: "running", startedAt: stamp, updatedAt: stamp,
    targetCommit, controlCommit: commit, researchSnapshotCommit: commit, inputs: values.inputs, outputs: [], models: [], prompts: [],
    toolCalls: [], costs: { apiUsd: 0, wallTimeSeconds: 0 }, attempts: [], evaluations: [], decisions: [], reflections: [],
    ...(values.parentRun ? { parentRun: values.parentRun } : {}),
    ...(values.parentAttempt ? { parentAttempt: values.parentAttempt } : {}),
  };
  const directory = join(root, "runs", id);
  await mkdir(join(directory, "attempts"), { recursive: true });
  await mkdir(join(directory, "evaluations"), { recursive: true });
  await Promise.all([
    atomicWrite(join(directory, "plan.md"), "# Plan\n\nPending.\n"),
    atomicWrite(join(directory, "research-delta.md"), "# Research Delta\n\nNone.\n"),
    atomicWrite(join(directory, "decision.md"), "# Decision\n\nPending.\n"),
    atomicWrite(join(directory, "reflection.md"), "# Reflection\n\nPending.\n"),
  ]);
  await writeYaml(join(directory, "run.yaml"), run);
  await rebuildRunIndex(root);
  return run;
}

export async function updateRun(root: string, run: RunRecord, patch: Partial<RunRecord>): Promise<RunRecord> {
  const updated = { ...run, ...patch, updatedAt: now() };
  await writeYaml(join(root, "runs", run.id, "run.yaml"), updated);
  await rebuildRunIndex(root);
  return updated;
}

export async function rebuildRunIndex(root: string): Promise<void> {
  const runsDir = join(root, "runs");
  const entries = await readdir(runsDir, { withFileTypes: true });
  const records: RunRecord[] = [];
  for (const entry of entries.filter((value) => value.isDirectory()).sort((a, b) => a.name.localeCompare(b.name))) {
    records.push(await readYaml<RunRecord>(join(runsDir, entry.name, "run.yaml")));
  }
  const lines = records.map((run) => `- [${run.id}](${run.id}/run.yaml): ${run.kind}, ${run.status}${run.parentRun ? `, parent ${run.parentRun}` : ""}`);
  await atomicWrite(join(runsDir, "index.md"), `# Run Index\n\n${lines.join("\n") || "No runs recorded."}\n`);
}

export async function rebuildCache(root: string): Promise<{ runs: number; concepts: number }> {
  const runEntries = (await readdir(join(root, "runs"), { withFileTypes: true })).filter((entry) => entry.isDirectory());
  const concepts: Array<{ id: string; path: string; type: string }> = [];
  for (const directory of ["resources", "observations", "entities", "claims", "relationships", "topics", "reports"]) {
    for (const name of (await readdir(join(root, "research", "okf", directory))).filter((value) => value.endsWith(".md"))) {
      const path = join(root, "research", "okf", directory, name);
      const match = (await readFile(path, "utf8")).match(/^---\n[\s\S]*?^type:\s*["']?([^\n"']+)/m);
      concepts.push({ id: name.slice(0, -3), path, type: match?.[1]?.trim() || "unknown" });
    }
  }
  const { DatabaseSync } = await import("node:sqlite");
  const database = new DatabaseSync(join(root, "cache", "registry.sqlite"));
  try {
    database.exec("DROP TABLE IF EXISTS runs; DROP TABLE IF EXISTS concepts; CREATE TABLE runs (id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL, path TEXT NOT NULL); CREATE TABLE concepts (id TEXT PRIMARY KEY, type TEXT NOT NULL, path TEXT NOT NULL);");
    const insertRun = database.prepare("INSERT INTO runs VALUES (?, ?, ?, ?)");
    for (const entry of runEntries) {
      const record = await readYaml<RunRecord>(join(root, "runs", entry.name, "run.yaml"));
      insertRun.run(record.id, record.kind, record.status, join(root, "runs", entry.name, "run.yaml"));
    }
    const insertConcept = database.prepare("INSERT INTO concepts VALUES (?, ?, ?)");
    for (const concept of concepts) insertConcept.run(concept.id, concept.type, concept.path);
  } finally { database.close(); }
  return { runs: runEntries.length, concepts: concepts.length };
}
