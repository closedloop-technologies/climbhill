import { access, mkdir, readFile } from "node:fs/promises";
import { basename, join, resolve } from "node:path";
import { constants } from "node:fs";
import { atomicWrite, frontmatter, now, readYaml, shortId, writeYaml } from "./io.js";
import { findWorktree, git, gitCommonDir, repositoryIdentity, resolveRepo } from "./git.js";
import { JOB_SCHEMA, OKF_SCHEMA, type JobPointer, type JobRecord } from "./types.js";

const DEFAULT_BUDGETS = {
  maxApiCostUsd: 5,
  maxWallTimeSeconds: 900,
  maxAttemptConcurrency: 2,
  maxResearchConcurrency: 2,
};

async function exists(path: string): Promise<boolean> {
  try { await access(path, constants.F_OK); return true; } catch { return false; }
}

function slugify(value: string): string {
  const slug = value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  if (!slug) throw new Error("--job must contain at least one letter or number");
  return slug;
}

export async function initializeJob(options: {
  target: string; control: string; location: string; job: string; objective?: string;
}): Promise<{ job: JobRecord; controlWorktree: string; pointerPath: string }> {
  const target = await resolveRepo(options.target);
  const control = await resolveRepo(options.control);
  const targetIdentity = await repositoryIdentity(target);
  const controlIdentity = await repositoryIdentity(control);
  const slug = slugify(options.job);

  const pointerDirectory = join(target, ".climbhill", "jobs");
  if (await exists(pointerDirectory)) {
    for (const file of await import("node:fs/promises").then((fs) => fs.readdir(pointerDirectory))) {
      const pointer = await readYaml<JobPointer>(join(pointerDirectory, file));
      if (pointer.control.id === controlIdentity.id && pointer.jobId.startsWith(`${slug}-`)) {
        throw new Error(`job '${pointer.jobId}' already exists for this target and control repository`);
      }
    }
  }

  let id = `${slug}-${shortId()}`;
  while (await exists(join(resolve(options.location), id))) id = `${slug}-${shortId()}`;
  const branch = `climbhill/${id}`;
  const worktree = join(resolve(options.location), id);
  const baseCommit = await git(control, ["rev-parse", "HEAD"]);
  await mkdir(resolve(options.location), { recursive: true });
  await git(control, ["branch", branch, baseCommit]);
  try {
    await git(control, ["worktree", "add", worktree, branch]);
  } catch (error) {
    await git(control, ["branch", "-D", branch]).catch(() => undefined);
    throw error;
  }

  const job: JobRecord = {
    schema: JOB_SCHEMA,
    okfSchema: OKF_SCHEMA,
    id,
    slug,
    objective: options.objective?.trim() || options.job,
    createdAt: now(),
    target: targetIdentity,
    control: controlIdentity,
    baseCommit,
    controlBranch: branch,
    budgets: DEFAULT_BUDGETS,
    policy: {
      allowedPaths: ["**"],
      deniedPaths: [".env", ".env.*", "**/secrets/**"],
      approvalRequiredPaths: [".github/**", "infra/**", "security/**"],
      requiredEvaluations: [],
      humanApprovalRequired: ["promotion", "policy-relaxation", "ci", "infrastructure", "security", "deployment"],
    },
  };

  const root = join(worktree, ".climbhill", id);
  const directories = ["research/raw", "research/okf/resources", "research/okf/observations", "research/okf/entities", "research/okf/claims", "research/okf/relationships", "research/okf/topics", "research/okf/reports", "runs", "cache"];
  await Promise.all(directories.map((directory) => mkdir(join(root, directory), { recursive: true })));
  await writeYaml(join(root, "job.yaml"), job);
  const controlIgnorePath = join(worktree, ".gitignore");
  const controlIgnore = await readFile(controlIgnorePath, "utf8").catch(() => "");
  const cachePattern = `.climbhill/${id}/cache/**`;
  if (!controlIgnore.split("\n").includes(cachePattern)) await atomicWrite(controlIgnorePath, `${controlIgnore}${controlIgnore.endsWith("\n") || !controlIgnore ? "" : "\n"}${cachePattern}\n`);
  await atomicWrite(join(root, "research/okf/index.md"), "# Knowledge Index\n\nNo concepts have been indexed yet.\n");
  await atomicWrite(join(root, "research/okf/log.md"), `# Knowledge Log\n\n- ${job.createdAt}: initialized ${id}.\n`);
  await atomicWrite(join(root, "research/okf/method.md"), frontmatter({ type: "method", schema: OKF_SCHEMA }, "# Method\n\nEvidence is ingested, derived source-locally, and reconciled explicitly."));
  await atomicWrite(join(root, "runs/index.md"), "# Run Index\n\nNo runs recorded.\n");

  const pointer: JobPointer = { schema: "climbhill.pointer/v1", jobId: id, control: controlIdentity, controlBranch: branch };
  const pointerPath = join(pointerDirectory, `${id}.yaml`);
  await writeYaml(pointerPath, pointer);
  await writeYaml(join(await gitCommonDir(target), "climbhill-locators", `${id}.yaml`), { controlRepository: control });
  await configureRawStorage(worktree, id);
  return { job, controlWorktree: worktree, pointerPath };
}

async function configureRawStorage(worktree: string, jobId: string): Promise<void> {
  const pattern = `.climbhill/${jobId}/research/raw/**`;
  try {
    await new Promise<void>((resolvePromise, reject) => {
      import("node:child_process").then(({ execFile }) => execFile("git", ["lfs", "version"], (error) => error ? reject(error) : resolvePromise()));
    });
    await git(worktree, ["lfs", "track", pattern]);
  } catch {
    const ignorePath = join(worktree, ".gitignore");
    const existing = await readFile(ignorePath, "utf8").catch(() => "");
    if (!existing.split("\n").includes(pattern)) await atomicWrite(ignorePath, `${existing}${existing.endsWith("\n") || !existing ? "" : "\n"}${pattern}\n`);
    await atomicWrite(join(worktree, ".climbhill", jobId, "research", "raw", "README.md"), "# Raw evidence storage\n\nGit LFS was unavailable during initialization. Raw artifacts are ignored. Install Git LFS, remove this ignore rule, and run `git lfs track` for this directory before committing raw evidence.\n");
  }
}

export async function discoverJob(target: string, requestedId?: string): Promise<{ job: JobRecord; root: string; worktree: string; targetRepository: string }> {
  const repo = await resolveRepo(target);
  const pointerDir = join(repo, ".climbhill", "jobs");
  const files = (await import("node:fs/promises").then((fs) => fs.readdir(pointerDir))).filter((name) => name.endsWith(".yaml"));
  const selected = requestedId ? files.find((name) => name === `${requestedId}.yaml`) : files.length === 1 ? files[0] : undefined;
  if (!selected) throw new Error(requestedId ? `job '${requestedId}' was not found` : `expected exactly one job pointer, found ${files.length}; pass --job-id`);
  const pointer = await readYaml<JobPointer>(join(pointerDir, selected));
  const locator = await readYaml<{ controlRepository: string }>(join(await gitCommonDir(repo), "climbhill-locators", `${pointer.jobId}.yaml`));
  const controlIdentity = await repositoryIdentity(locator.controlRepository);
  if (controlIdentity.id !== pointer.control.id) throw new Error(`local control repository does not match portable identity for ${pointer.jobId}`);
  const worktree = await findWorktree(locator.controlRepository, pointer.controlBranch);
  if (!worktree) throw new Error(`control worktree for ${pointer.controlBranch} is not registered; recover or add the worktree`);
  const root = join(worktree, ".climbhill", pointer.jobId);
  return { job: await readYaml<JobRecord>(join(root, "job.yaml")), root, worktree, targetRepository: repo };
}

export async function recoverJob(options: { target: string; control: string; location: string; jobId: string }): Promise<{ job: JobRecord; controlWorktree: string; pointerPath: string }> {
  const target = await resolveRepo(options.target);
  const control = await resolveRepo(options.control);
  const branch = `climbhill/${options.jobId}`;
  await git(control, ["show-ref", "--verify", `refs/heads/${branch}`]);
  let worktree = await findWorktree(control, branch);
  if (!worktree) {
    worktree = join(resolve(options.location), options.jobId);
    if (await exists(worktree)) throw new Error(`recovery location already exists: ${worktree}`);
    await mkdir(resolve(options.location), { recursive: true });
    await git(control, ["worktree", "add", worktree, branch]);
  }
  const root = join(worktree, ".climbhill", options.jobId);
  const job = await readYaml<JobRecord>(join(root, "job.yaml"));
  if (job.id !== options.jobId) throw new Error("control branch job identity does not match --job-id");
  const targetIdentity = await repositoryIdentity(target);
  const controlIdentity = await repositoryIdentity(control);
  if (job.target.id !== targetIdentity.id || job.control.id !== controlIdentity.id) throw new Error("recovery repositories do not match the job identities");
  const pointerPath = join(target, ".climbhill", "jobs", `${job.id}.yaml`);
  await writeYaml(pointerPath, { schema: "climbhill.pointer/v1", jobId: job.id, control: job.control, controlBranch: job.controlBranch } satisfies JobPointer);
  await writeYaml(join(await gitCommonDir(target), "climbhill-locators", `${job.id}.yaml`), { controlRepository: control });
  return { job, controlWorktree: worktree, pointerPath };
}
