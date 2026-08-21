#!/usr/bin/env node
import { resolve } from "node:path";
import { readFile } from "node:fs/promises";
import { initializeJob, discoverJob, recoverJob } from "./job.js";
import { addSource, updateResource } from "./source.js";
import { derivePending, deriveResource } from "./derive.js";
import { buildGraph, inspectGraph } from "./graph.js";
import { createRun, rebuildCache, updateRun } from "./run-store.js";
import { now } from "./io.js";
import { runResearch } from "./research.js";
import { validateOkf } from "./okf-validator.js";
import type { SourceType } from "./types.js";
import { attachAttemptPatch, compareAttempts, decideAttempt, evaluateAttempt, loadRun, planImprovement, promoteSkill, recordReflection } from "./improvement.js";
import { classifyPaths, updateBudgets } from "./policy.js";
import { modelCost, OPENAI_MODEL, OPENAI_PRICING } from "./model-cost.js";

const HELP = `ClimbHill local-first agentic workflow CLI

Usage:
  climbhill init --target <repo> --control <repo> --location <path> --job <slug> [--objective <text>]
  climbhill recover --target <repo> --control <repo> --location <path> --job-id <id>
  climbhill add <url-or-file> [--type <type>] [--no-derive] [--target <repo>] [--job-id <id>]
  climbhill derive [--resource <id>] [--append-prompt <text>] [--prompt-file <path>]
  climbhill graph build|inspect
  climbhill research <question> [--resume <run-id>] [--local-only] [--max-api-cost <usd>] [--max-wall-time <seconds>]
  climbhill run --goal <text> [--attempts <count>] [--parent-run <id>] [--parent-attempt <id>]
  climbhill evaluate --run <id> --attempt <id> --command <command>
  climbhill compare --run <id>
  climbhill attempt attach-patch --run <id> --attempt <id> --patch <file> [--head-commit <sha>]
  climbhill decision --run <id> --attempt <id> --decision promote|reject --rationale <text> [--approve]
  climbhill reflect --run <id> --text <reflection>
  climbhill skill promote <directory> --run <id> --concept <ids> --evaluation <ids> --approve
  climbhill policy set-budgets [--max-api-cost <usd>] [--max-wall-time <seconds>] --rationale <text> [--approve]
  climbhill policy check <target-path>...
  climbhill cache rebuild
  climbhill okf validate

Source types: file, pdf, webpage, youtube, arxiv`;

interface ParsedArgs { positional: string[]; options: Map<string, string | boolean> }

function parse(values: string[]): ParsedArgs {
  const positional: string[] = [];
  const options = new Map<string, string | boolean>();
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (!value.startsWith("--")) { positional.push(value); continue; }
    const [key, inline] = value.slice(2).split("=", 2);
    if (inline !== undefined) options.set(key, inline);
    else if (values[index + 1] && !values[index + 1].startsWith("--")) options.set(key, values[++index]);
    else options.set(key, true);
  }
  return { positional, options };
}

function option(args: ParsedArgs, name: string, fallback?: string): string | undefined {
  const value = args.options.get(name);
  if (value === true) throw new Error(`--${name} requires a value`);
  return typeof value === "string" ? value : fallback;
}

function required(args: ParsedArgs, name: string): string {
  const value = option(args, name);
  if (!value) throw new Error(`--${name} is required`);
  return value;
}

function numberOption(args: ParsedArgs, name: string, fallback: number): number {
  const value = Number(option(args, name, String(fallback)));
  if (!Number.isFinite(value) || value < 0) throw new Error(`--${name} must be a non-negative number`);
  return value;
}

function listOption(args: ParsedArgs, name: string): string[] {
  return (option(args, name, "") || "").split(",").map((value) => value.trim()).filter(Boolean);
}

async function context(args: ParsedArgs) {
  return discoverJob(resolve(option(args, "target", ".")!), option(args, "job-id"));
}

export async function main(argv = process.argv.slice(2)): Promise<number> {
  const command = argv[0];
  if (!command || command === "help" || command === "--help" || command === "-h") { console.log(HELP); return 0; }
  const args = parse(argv.slice(1));
  if (command === "init") {
    const initialized = await initializeJob({ target: required(args, "target"), control: required(args, "control"), location: required(args, "location"), job: required(args, "job"), objective: option(args, "objective") });
    console.log(`Initialized ${initialized.job.id}\nControl worktree: ${initialized.controlWorktree}\nPortable pointer: ${initialized.pointerPath}`);
    return 0;
  }
  if (command === "recover") {
    const recovered = await recoverJob({ target: required(args, "target"), control: required(args, "control"), location: required(args, "location"), jobId: required(args, "job-id") });
    console.log(`Recovered ${recovered.job.id}\nControl worktree: ${recovered.controlWorktree}\nPortable pointer: ${recovered.pointerPath}`); return 0;
  }
  if (command === "add") {
    if (args.positional.length !== 1) throw new Error("add retrieves exactly one source");
    const type = option(args, "type") as SourceType | undefined;
    if (type && !["file", "pdf", "webpage", "youtube", "arxiv"].includes(type)) throw new Error(`unsupported source type: ${type}`);
    const job = await context(args);
    const result = await addSource(job.root, args.positional[0], type);
    if (result.duplicate) { console.log(`${result.resource.id} (unchanged)`); return 0; }
    let run = await createRun(job.root, job.worktree, { kind: "ingest", inputs: { source: args.positional[0], type: result.resource.type } }, job.targetRepository);
    run = await updateRun(job.root, run, { outputs: [result.resource.id], status: "completed", completedAt: now(), stoppingReason: "ingested" });
    if (args.options.has("no-derive")) {
      result.resource.derivationStatus = "skipped";
      await updateResource(job.root, result.resource);
      console.log(result.resource.id);
      return 0;
    }
    try {
      const derived = await deriveResource(job.root, result.resource.id);
      result.resource.derivationStatus = "succeeded";
      await updateResource(job.root, result.resource);
      if (derived.usage) {
        run = await updateRun(job.root, run, { models: [OPENAI_MODEL], costs: { apiUsd: modelCost(derived.usage), wallTimeSeconds: run.costs.wallTimeSeconds }, toolCalls: [{ at: now(), tool: "baml", function: "DeriveSource", model: OPENAI_MODEL, usage: derived.usage, pricing: OPENAI_PRICING }] });
      }
      console.log(`${result.resource.id}: ${derived.observations.length} observations`);
      return 0;
    } catch (error) {
      result.resource.derivationStatus = "failed";
      result.resource.derivationError = error instanceof Error ? error.message : String(error);
      await updateResource(job.root, result.resource);
      console.error(`Ingestion succeeded but derivation failed: ${result.resource.derivationError}`);
      return 2;
    }
  }
  if (command === "derive") {
    const job = await context(args);
    const derivationOptions = { appendPrompt: option(args, "append-prompt"), promptFile: option(args, "prompt-file") };
    const resource = option(args, "resource");
    const results = resource ? [await deriveResource(job.root, resource, derivationOptions)].map((result) => ({ resourceId: resource, count: result.observations.length, cached: result.cached, ...(result.usage ? { usage: result.usage } : {}) })) : await derivePending(job.root, derivationOptions);
    const generated = results.filter((result) => !result.cached);
    if (generated.length) {
      let run = await createRun(job.root, job.worktree, { kind: "derive", inputs: { resources: generated.map((result) => result.resourceId), appendPrompt: derivationOptions.appendPrompt, promptFile: derivationOptions.promptFile } }, job.targetRepository);
      const usages = generated.flatMap((result) => result.usage ? [result.usage] : []);
      const cost = usages.reduce((total, usage) => total + modelCost(usage), 0);
      run = await updateRun(job.root, run, { status: "completed", completedAt: now(), stoppingReason: "derived", outputs: generated.map((result) => result.resourceId), models: usages.length ? [OPENAI_MODEL] : [], costs: { apiUsd: cost, wallTimeSeconds: run.costs.wallTimeSeconds }, toolCalls: usages.map((usage) => ({ at: now(), tool: "baml", function: "DeriveSource", model: OPENAI_MODEL, usage, pricing: OPENAI_PRICING })) });
    }
    for (const result of results) console.log(`${result.resourceId}\t${result.count}\t${result.cached ? "cached" : "generated"}`);
    return 0;
  }
  if (command === "graph") {
    const action = args.positional[0];
    const job = await context(args);
    if (action === "build") {
      const result = await buildGraph(job.root);
      if (!result.cached) {
        let run = await createRun(job.root, job.worktree, { kind: "graph", inputs: { observationHash: result.summary.inputHash } }, job.targetRepository);
        run = await updateRun(job.root, run, { status: "completed", completedAt: now(), stoppingReason: "graph-built", outputs: result.summary.concepts.map((concept) => concept.id) });
      }
      console.log(`${result.cached ? "unchanged" : "built"}: ${result.summary.created} concepts, ${result.summary.merged} merged, ${result.summary.unresolved} unresolved`);
      return 0;
    }
    if (action === "inspect") { console.log(JSON.stringify(await inspectGraph(job.root), null, 2)); return 0; }
    throw new Error("graph requires build or inspect");
  }
  if (command === "research") {
    const job = await context(args);
    const resumeRunId = option(args, "resume");
    const prior = resumeRunId ? await loadRun(job.root, resumeRunId) : undefined;
    const question = args.positional.join(" ") || (prior?.inputs.question as string | undefined);
    if (!question) throw new Error("research requires a question or --resume <run-id>");
    const result = await runResearch(job.root, job.worktree, question, { localOnly: args.options.has("local-only") || Boolean(prior?.inputs.localOnly), maxApiCostUsd: numberOption(args, "max-api-cost", job.job.budgets.maxApiCostUsd), maxWallTimeSeconds: numberOption(args, "max-wall-time", job.job.budgets.maxWallTimeSeconds), targetRepository: job.targetRepository, resumeRunId });
    console.log(`${result.runId}: ${result.status}${result.answerPath ? `\n${result.answerPath}` : ""}`);
    return result.status === "completed" ? 0 : 2;
  }
  if (command === "run") {
    const job = await context(args);
    const run = await planImprovement(job.root, job.worktree, job.targetRepository, { goal: required(args, "goal"), attempts: numberOption(args, "attempts", 1), parentRun: option(args, "parent-run"), parentAttempt: option(args, "parent-attempt") });
    console.log(`${run.id}\n${run.attempts.join("\n")}`); return 0;
  }
  if (command === "evaluate") {
    const job = await context(args);
    const evaluation = await evaluateAttempt(job.root, job.targetRepository, required(args, "run"), required(args, "attempt"), required(args, "command"), numberOption(args, "max-wall-time", job.job.budgets.maxWallTimeSeconds));
    console.log(`${evaluation.id}: ${evaluation.status}`); return evaluation.status === "passed" ? 0 : 2;
  }
  if (command === "compare") {
    const job = await context(args);
    for (const row of await compareAttempts(job.root, required(args, "run"))) console.log(`${row.attempt.id}\t${row.passed}\t${row.failed}\t${row.attempt.status}\t${row.attempt.summary}`);
    return 0;
  }
  if (command === "attempt" && args.positional[0] === "attach-patch") {
    const job = await context(args);
    console.log(await attachAttemptPatch(job.root, required(args, "run"), required(args, "attempt"), required(args, "patch"), option(args, "head-commit"))); return 0;
  }
  if (command === "decision") {
    const decision = required(args, "decision");
    if (decision !== "promote" && decision !== "reject") throw new Error("--decision must be promote or reject");
    const job = await context(args);
    await decideAttempt(job.root, required(args, "run"), required(args, "attempt"), decision, required(args, "rationale"), args.options.has("approve"));
    console.log(`Recorded ${decision} decision`); return 0;
  }
  if (command === "reflect") {
    const job = await context(args);
    console.log(await recordReflection(job.root, required(args, "run"), required(args, "text"))); return 0;
  }
  if (command === "skill" && args.positional[0] === "promote") {
    if (!args.positional[1]) throw new Error("skill promote requires a source directory");
    const job = await context(args);
    const destination = await promoteSkill(job.root, job.targetRepository, job.job, { source: args.positional[1], name: option(args, "name"), concepts: listOption(args, "concept"), runId: required(args, "run"), evaluations: listOption(args, "evaluation"), approved: args.options.has("approve") });
    console.log(destination); return 0;
  }
  if (command === "policy" && args.positional[0] === "set-budgets") {
    const job = await context(args);
    const changes: Partial<typeof job.job.budgets> = {};
    if (args.options.has("max-api-cost")) changes.maxApiCostUsd = numberOption(args, "max-api-cost", job.job.budgets.maxApiCostUsd);
    if (args.options.has("max-wall-time")) changes.maxWallTimeSeconds = numberOption(args, "max-wall-time", job.job.budgets.maxWallTimeSeconds);
    if (args.options.has("max-attempt-concurrency")) changes.maxAttemptConcurrency = numberOption(args, "max-attempt-concurrency", job.job.budgets.maxAttemptConcurrency);
    if (args.options.has("max-research-concurrency")) changes.maxResearchConcurrency = numberOption(args, "max-research-concurrency", job.job.budgets.maxResearchConcurrency);
    await updateBudgets(job.root, job.job, changes, required(args, "rationale"), args.options.has("approve"));
    console.log("Recorded budget policy decision"); return 0;
  }
  if (command === "policy" && args.positional[0] === "check") {
    const job = await context(args);
    if (args.positional.length < 2) throw new Error("policy check requires at least one target path");
    const results = classifyPaths(job.job, args.positional.slice(1));
    for (const result of results) console.log(`${result.path}\t${result.classification}${result.pattern ? `\t${result.pattern}` : ""}`);
    return results.some((result) => result.classification !== "allowed") ? 3 : 0;
  }
  if (command === "cache" && args.positional[0] === "rebuild") {
    const job = await context(args); console.log(JSON.stringify(await rebuildCache(job.root))); return 0;
  }
  if (command === "okf" && args.positional[0] === "validate") {
    const job = await context(args); const result = await validateOkf(job.root);
    result.errors.forEach((error) => console.error(error)); console.log(`${result.concepts} concepts validated`); return result.errors.length ? 2 : 0;
  }
  throw new Error(`unknown command '${command}'\n\n${HELP}`);
}

if (require.main === module) {
  main().then((code) => { process.exitCode = code; }).catch((error) => { console.error(error instanceof Error ? error.message : String(error)); process.exitCode = 1; });
}
