import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { b } from "./baml_client/async_client.js";
import { addSource } from "./source.js";
import { deriveResource } from "./derive.js";
import { atomicWrite, now } from "./io.js";
import { createRun, updateRun } from "./run-store.js";
import { readYaml } from "./io.js";
import type { RunRecord } from "./types.js";
import { Collector } from "@boundaryml/baml";
import { modelCost, OPENAI_MODEL, OPENAI_PRICING, type TokenUsage } from "./model-cost.js";

interface ResearchClient {
  plan(question: string, corpus: string): Promise<{ existing_evidence_summary: string; missing_evidence: string[]; searches: string[]; completion_criteria: string[]; usage?: TokenUsage }>;
  synthesize(question: string, concepts: string): Promise<{ answer: string; concept_ids: string[]; remaining_uncertainties: string[]; usage?: TokenUsage }>;
}

interface SearchClient { search(query: string, remainingCost: number): Promise<{ urls: string[]; cost: number; raw: unknown }> }

const modelClient: ResearchClient = {
  async plan(question, local) {
    const collector = new Collector("climbhill-research-plan");
    const result = await b.PlanResearch(question, local, { collector });
    return { ...result, usage: { inputTokens: collector.usage.inputTokens || 0, outputTokens: collector.usage.outputTokens || 0, cachedInputTokens: collector.usage.cachedInputTokens || 0 } };
  },
  async synthesize(question, local) {
    const collector = new Collector("climbhill-research-synthesis");
    const result = await b.SynthesizeResearch(question, local, { collector });
    return { ...result, usage: { inputTokens: collector.usage.inputTokens || 0, outputTokens: collector.usage.outputTokens || 0, cachedInputTokens: collector.usage.cachedInputTokens || 0 } };
  },
};

async function corpus(root: string): Promise<string> {
  const portions: string[] = [];
  for (const directory of ["resources", "observations", "entities", "claims", "relationships"]) {
    for (const name of (await readdir(join(root, "research", "okf", directory)).catch(() => [])).filter((value) => value.endsWith(".md")).sort()) {
      portions.push(`CONCEPT ${name.slice(0, -3)}\n${await readFile(join(root, "research", "okf", directory, name), "utf8")}`);
    }
  }
  return portions.join("\n\n");
}

async function tavilySearch(query: string, remainingCost: number): Promise<{ urls: string[]; cost: number; raw: unknown }> {
  const estimatedCost = Number(process.env.CLIMBHILL_TAVILY_COST_USD || "0.008");
  if (remainingCost < estimatedCost) throw new Error("api-cost-budget-reached");
  const apiKey = process.env.TAVILY_API_KEY;
  if (!apiKey) throw new Error("normal research requires TAVILY_API_KEY or --local-only");
  const response = await fetch("https://api.tavily.com/search", { method: "POST", headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" }, body: JSON.stringify({ query, search_depth: "basic", max_results: 3, include_answer: false, include_raw_content: false }), signal: AbortSignal.timeout(60_000) });
  if (!response.ok) throw new Error(`deep-research-tavily search failed (${response.status})`);
  const raw = await response.json() as { results?: Array<{ url?: string }> };
  return { urls: (raw.results || []).flatMap((result) => result.url ? [result.url] : []), cost: estimatedCost, raw };
}

export async function runResearch(root: string, worktree: string, question: string, options: {
  localOnly?: boolean;
  maxApiCostUsd: number;
  maxWallTimeSeconds: number;
  targetRepository?: string;
  resumeRunId?: string;
  client?: ResearchClient;
  searchClient?: SearchClient;
}): Promise<{ runId: string; status: string; answerPath?: string }> {
  const started = Date.now();
  let run: RunRecord = options.resumeRunId ? await readYaml<RunRecord>(join(root, "runs", options.resumeRunId, "run.yaml")) : await createRun(root, worktree, { kind: "research", inputs: { question, localOnly: Boolean(options.localOnly), budgets: { maxApiCostUsd: options.maxApiCostUsd, maxWallTimeSeconds: options.maxWallTimeSeconds } } }, options.targetRepository);
  if (run.kind !== "research") throw new Error(`${run.id} is not a research run`);
  if (options.resumeRunId) run = await updateRun(root, run, { status: "running", stoppingReason: undefined });
  const runDirectory = join(root, "runs", run.id);
  const baseWallTime = run.costs.wallTimeSeconds;
  const elapsed = () => (Date.now() - started) / 1000;
  const timedOut = () => elapsed() >= options.maxWallTimeSeconds;
  const client = options.client || modelClient;
  const searchClient = options.searchClient || { search: tavilySearch };
  const heartbeat = setInterval(() => { void updateRun(root, run, { costs: { ...run.costs, wallTimeSeconds: baseWallTime + elapsed() } }).catch(() => undefined); }, 1000);
  try {
    const local = await corpus(root);
    run = await updateRun(root, run, { costs: { ...run.costs, wallTimeSeconds: baseWallTime + elapsed() }, prompts: [...new Set([...run.prompts, "PlanResearch"])] });
    if (timedOut()) throw new Error("wall-time-budget-reached");
    if (run.costs.apiUsd >= options.maxApiCostUsd) throw new Error("api-cost-budget-reached");
    const plan = await client.plan(question, local);
    if (plan.usage) {
      run.costs.apiUsd += modelCost(plan.usage);
      run.toolCalls.push({ at: now(), tool: "baml", function: "PlanResearch", model: OPENAI_MODEL, usage: plan.usage, pricing: OPENAI_PRICING });
      run = await updateRun(root, run, { costs: { ...run.costs, wallTimeSeconds: baseWallTime + elapsed() }, toolCalls: run.toolCalls, models: [...new Set([...run.models, OPENAI_MODEL])] });
      if (run.costs.apiUsd >= options.maxApiCostUsd) throw new Error("api-cost-budget-reached");
    }
    await atomicWrite(join(runDirectory, "plan.md"), `# Plan\n\n## Existing evidence\n\n${plan.existing_evidence_summary}\n\n## Missing evidence\n\n${plan.missing_evidence.map((value: string) => `- ${value}`).join("\n") || "- None"}\n\n## Searches\n\n${plan.searches.map((value: string) => `- ${value}`).join("\n") || "- None"}\n`);
    if (!options.localOnly) {
      for (const query of plan.searches) {
        if (run.toolCalls.some((value) => value.tool === "deep-research-tavily" && value.query === query)) continue;
        if (timedOut()) throw new Error("wall-time-budget-reached");
        const search = await searchClient.search(query, options.maxApiCostUsd - run.costs.apiUsd);
        run.costs.apiUsd += search.cost;
        run.toolCalls.push({ at: now(), tool: "deep-research-tavily", query, urls: search.urls });
        run = await updateRun(root, run, { costs: { ...run.costs, wallTimeSeconds: baseWallTime + elapsed() }, toolCalls: run.toolCalls });
        for (const url of search.urls) {
          const added = await addSource(root, url, "webpage");
          if (!added.duplicate) await deriveResource(root, added.resource.id);
          run.outputs.push(added.resource.id);
        }
      }
    }
    if (timedOut()) throw new Error("wall-time-budget-reached");
    const evidence = await corpus(root);
    if (run.costs.apiUsd >= options.maxApiCostUsd) throw new Error("api-cost-budget-reached");
    const answer = await client.synthesize(question, evidence);
    if (answer.usage) {
      run.costs.apiUsd += modelCost(answer.usage);
      run.toolCalls.push({ at: now(), tool: "baml", function: "SynthesizeResearch", model: OPENAI_MODEL, usage: answer.usage, pricing: OPENAI_PRICING });
    }
    const answerPath = join(runDirectory, "answer.md");
    await atomicWrite(answerPath, `# Answer\n\n${answer.answer}\n\n## Local citations\n\n${answer.concept_ids.map((value: string) => `- ${value}`).join("\n") || "- None"}\n\n## Remaining uncertainties\n\n${answer.remaining_uncertainties.map((value: string) => `- ${value}`).join("\n") || "- None"}\n`);
    run = await updateRun(root, run, { status: "completed", completedAt: now(), stoppingReason: run.costs.apiUsd >= options.maxApiCostUsd ? "api-cost-budget-reached-after-final-answer" : "completed", outputs: [...run.outputs, answerPath], costs: { ...run.costs, wallTimeSeconds: baseWallTime + elapsed() }, prompts: [...new Set([...run.prompts, "SynthesizeResearch"])], toolCalls: run.toolCalls, models: [...new Set([...run.models, ...(answer.usage ? [OPENAI_MODEL] : [])])] });
    return { runId: run.id, status: run.status, answerPath };
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    await atomicWrite(join(runDirectory, "partial.md"), `# Partial research\n\nStopped: ${reason}\n\nCompleted outputs:\n${run.outputs.map((value) => `- ${value}`).join("\n") || "- None"}\n`);
    run = await updateRun(root, run, { status: reason.includes("budget-reached") ? "partial" : "failed", stoppingReason: reason, costs: { ...run.costs, wallTimeSeconds: baseWallTime + elapsed() } });
    return { runId: run.id, status: run.status };
  } finally { clearInterval(heartbeat); }
}
