export type Provider = "anthropic" | "openai" | "xai" | "claude" | "codex" | "agent";

export interface ModelInfo {
  id: string;
  provider: Provider;
  name: string;
  slug: string;
  color: string;
  icon: string;
}

export interface CategoryInfo {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon: string;
  weight: number;
}

export interface TestInfo {
  id: string;
  name: string;
  categoryId: string;
  description: string;
}

export interface TestResult {
  testId: string;
  name: string;
  score: number;
  latencyMs: number;
  tokenCount?: number | null;
}

export interface CategoryScore {
  avgScore: number | null;
  testCount: number;
  tests: TestResult[];
}

export interface ModelRunResult {
  compositeScore: number | null;
  rank: number | null;
  totalTokens?: number | null;
  avgTokensPerTest?: number | null;
  categories: Record<string, CategoryScore>;
}

export interface LatestRun {
  runId: string;
  startedAt: string;
  completedAt: string;
  schedule: "daily" | "morning" | "afternoon" | "night";
  models: Record<string, ModelRunResult>;
}

export interface Synopsis {
  day: { modelId: string; name: string; score: number; change: number };
  week: { modelId: string; name: string; score: number; change: number };
  month: { modelId: string; name: string; score: number; change: number };
  updatedAt: string;
}

export interface HistoryEntry {
  timestamp: string;
  compositeScore: number | null;
  totalTokens?: number | null;
  categories: Record<string, number | null>;
}

export interface Regression {
  id: string;
  modelId: string;
  modelName: string;
  categoryId: string | null;
  categoryName: string | null;
  detectedAt: string;
  previousAvg: number;
  currentScore: number;
  dropPct: number;
  severity: "minor" | "moderate" | "major";
  windowDays: number;
  resolvedAt: string | null;
}

export interface Outage {
  id: string;
  provider: Provider;
  modelId: string | null;
  startedAt: string;
  endedAt: string | null;
  errorType: string;
  errorMessage: string;
  httpStatus: number | null;
  checkCount: number;
}

export interface ModelDetail {
  model: ModelInfo;
  current: ModelRunResult;
  history: HistoryEntry[];
  regressions: Regression[];
  outages: Outage[];
}

export interface CategoryDetail {
  category: CategoryInfo;
  tests: TestInfo[];
  models: Record<
    string,
    {
      currentScore: number | null;
      totalTokens?: number | null;
      avgTokensPerTest?: number | null;
      history: { timestamp: string; score: number | null }[];
    }
  >;
}

export interface TrendData {
  period: string;
  data: {
    timestamp: string;
    models: Record<string, number>;
  }[];
}

export interface RegressionData {
  active: Regression[];
  recent: Regression[];
}

export interface OutageData {
  current: Outage[];
  history: Outage[];
  uptime: Record<
    string,
    {
      "7d": number;
      "30d": number;
      "90d": number;
    }
  >;
}

export interface EvidenceData {
  test: {
    id: string;
    name: string;
    category: string;
    categoryName: string;
    description: string;
    prompt: string;
  };
  results: Record<
    string,
    {
      score: number;
      modelOutput: string;
      evalDetails: Record<string, unknown>;
      latencyMs: number;
      tokenCount: number | null;
      promptTokens: number | null;
      completionTokens: number | null;
      error: string | null;
    }
  >;
}

export type TimeRange = "day" | "week" | "month" | "year";
