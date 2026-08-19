import { execFile } from "node:child_process";
import { realpath } from "node:fs/promises";
import { promisify } from "node:util";
import { createHash } from "node:crypto";
import type { RepositoryIdentity } from "./types.js";

const execFileAsync = promisify(execFile);

export async function git(repo: string, args: string[]): Promise<string> {
  try {
    const { stdout } = await execFileAsync("git", ["-C", repo, ...args], { encoding: "utf8" });
    return stdout.trim();
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`git ${args.join(" ")} failed in ${repo}: ${detail}`);
  }
}

export async function repositoryIdentity(repo: string): Promise<RepositoryIdentity> {
  const common = await git(repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"]);
  let remote: string | undefined;
  try {
    remote = await git(repo, ["config", "--get", "remote.origin.url"]);
  } catch {
    remote = undefined;
  }
  const seed = remote || await git(repo, ["rev-list", "--max-parents=0", "HEAD"]);
  const id = createHash("sha256").update(seed).digest("hex");
  await realpath(common); // Ensure this is a valid repository identity source.
  return { id, ...(remote ? { remote } : {}) };
}

export async function gitCommonDir(repo: string): Promise<string> {
  return realpath(await git(repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"]));
}

export async function resolveRepo(repo: string): Promise<string> {
  return realpath(await git(repo, ["rev-parse", "--show-toplevel"]));
}

export async function findWorktree(repo: string, branch: string): Promise<string | undefined> {
  const lines = (await git(repo, ["worktree", "list", "--porcelain"])).split("\n");
  let path: string | undefined;
  for (const line of lines) {
    if (line.startsWith("worktree ")) path = line.slice(9);
    if (line === `branch refs/heads/${branch}`) return path;
  }
  return undefined;
}
