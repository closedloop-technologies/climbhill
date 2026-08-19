import { join } from "node:path";
import { now, shortId, writeYaml } from "./io.js";
import type { JobRecord } from "./types.js";

function globRegex(pattern: string): RegExp {
  const escaped = pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&").replaceAll("**", "\u0000").replaceAll("*", "[^/]*").replaceAll("\u0000", ".*");
  return new RegExp(`^${escaped}$`);
}

export function classifyPaths(job: JobRecord, paths: string[]): Array<{ path: string; classification: "allowed" | "denied" | "approval-required"; pattern?: string }> {
  return paths.map((path) => {
    if (path.startsWith("/") || path.split("/").includes("..") || path.includes("\\")) return { path, classification: "denied", pattern: "unsafe-path" };
    const denied = job.policy.deniedPaths.find((pattern) => globRegex(pattern).test(path));
    if (denied) return { path, classification: "denied", pattern: denied };
    const approval = job.policy.approvalRequiredPaths.find((pattern) => globRegex(pattern).test(path));
    if (approval) return { path, classification: "approval-required", pattern: approval };
    const allowed = job.policy.allowedPaths.find((pattern) => globRegex(pattern).test(path));
    return allowed ? { path, classification: "allowed", pattern: allowed } : { path, classification: "denied" };
  });
}

export async function updateBudgets(root: string, job: JobRecord, changes: Partial<JobRecord["budgets"]>, rationale: string, approved: boolean): Promise<JobRecord> {
  const next = { ...job.budgets, ...changes };
  for (const [name, value] of Object.entries(next)) if (!Number.isFinite(value) || value < 0) throw new Error(`${name} must be a non-negative number`);
  const relaxed = Object.entries(next).some(([name, value]) => value > job.budgets[name as keyof typeof job.budgets]);
  if (relaxed && !approved) throw new Error("budget increases are policy relaxations and require --approve");
  const updated: JobRecord = { ...job, budgets: next };
  await writeYaml(join(root, "job.yaml"), updated);
  const id = `policy-decision-${shortId()}`;
  await writeYaml(join(root, "decisions", `${id}.yaml`), { schema: "climbhill.policy-decision/v1", id, type: relaxed ? "policy-relaxation" : "policy-tightening", previous: job.budgets, next, rationale, humanApproved: approved, recordedAt: now() });
  return updated;
}
