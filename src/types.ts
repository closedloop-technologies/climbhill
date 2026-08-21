export const JOB_SCHEMA = "climbhill.job/v1";
export const RUN_SCHEMA = "climbhill.run/v1";
export const OKF_SCHEMA = "okf/0.2";

export type SourceType = "file" | "pdf" | "webpage" | "youtube" | "arxiv";

export interface RepositoryIdentity {
  id: string;
  remote?: string;
}

export interface BudgetPolicy {
  maxApiCostUsd: number;
  maxWallTimeSeconds: number;
  maxAttemptConcurrency: number;
  maxResearchConcurrency: number;
}

export interface JobRecord {
  schema: typeof JOB_SCHEMA;
  okfSchema: typeof OKF_SCHEMA;
  id: string;
  slug: string;
  objective: string;
  createdAt: string;
  target: RepositoryIdentity;
  control: RepositoryIdentity;
  baseCommit: string;
  controlBranch: string;
  budgets: BudgetPolicy;
  policy: {
    allowedPaths: string[];
    deniedPaths: string[];
    approvalRequiredPaths: string[];
    requiredEvaluations: string[];
    humanApprovalRequired: string[];
  };
}

export interface JobPointer {
  schema: "climbhill.pointer/v1";
  jobId: string;
  control: RepositoryIdentity;
  controlBranch: string;
}

export interface ResourceVersion {
  id: string;
  logicalId: string;
  version: number;
  type: SourceType;
  source: string;
  title: string;
  author?: string;
  publisher?: string;
  publishedAt?: string;
  retrievedAt: string;
  contentHash: string;
  rawPath: string;
  mediaType: string;
  metadata: Record<string, unknown>;
  derivationStatus: "pending" | "succeeded" | "failed" | "skipped";
  derivationError?: string;
}

export interface EvidenceLocator {
  kind: "line" | "page" | "timestamp" | "heading";
  value: string;
}

export interface Observation {
  id: string;
  type: "entity" | "fact" | "claim" | "procedure" | "relationship" | "recommendation" | "gap";
  text: string;
  resourceId: string;
  locator: EvidenceLocator;
  relationship?: { subject: string; type: string; object: string };
  generated: {
    at: string;
    identity: string;
    profile: string;
    model: string;
    schema: string;
    promptHash: string;
    chunkingPolicy: string;
    verified: false;
  };
}

export interface RunRecord {
  schema: typeof RUN_SCHEMA;
  id: string;
  kind: "ingest" | "derive" | "graph" | "research" | "improvement";
  status: "running" | "completed" | "partial" | "failed" | "rejected";
  startedAt: string;
  updatedAt: string;
  completedAt?: string;
  stoppingReason?: string;
  targetCommit: string;
  controlCommit: string;
  researchSnapshotCommit?: string;
  parentRun?: string;
  parentAttempt?: string;
  inputs: Record<string, unknown>;
  outputs: string[];
  models: string[];
  prompts: string[];
  toolCalls: Array<Record<string, unknown>>;
  costs: { apiUsd: number; wallTimeSeconds: number };
  attempts: string[];
  evaluations: string[];
  decisions: string[];
  reflections: string[];
}
