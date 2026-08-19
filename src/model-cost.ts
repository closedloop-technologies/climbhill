export const OPENAI_MODEL = "gpt-5.1-2025-11-13";
export const OPENAI_PRICING = {
  source: "https://developers.openai.com/api/docs/models/gpt-5.1",
  unit: "USD per 1M tokens",
  input: 1.25,
  cachedInput: 0.125,
  output: 10,
} as const;

export interface TokenUsage { inputTokens: number; outputTokens: number; cachedInputTokens: number }

export function modelCost(usage: TokenUsage): number {
  const uncached = Math.max(0, usage.inputTokens - usage.cachedInputTokens);
  return (uncached * OPENAI_PRICING.input + usage.cachedInputTokens * OPENAI_PRICING.cachedInput + usage.outputTokens * OPENAI_PRICING.output) / 1_000_000;
}
