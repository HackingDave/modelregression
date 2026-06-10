import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import { getCategoryDetail, getAllCategorySlugs } from "@/lib/data";
import { getModel } from "@/lib/models";
import { TOKEN_EFFICIENCY_CATEGORY_ID } from "@/lib/categories";
import {
  cn,
  formatScore,
  getScoreColor,
  formatTokens,
} from "@/lib/utils";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import { AnimatedCounter } from "@/components/shared/animated-counter";
import { PerformanceLineChart } from "@/components/charts/performance-line-chart";
import { Sparkline } from "@/components/charts/sparkline";
import {
  ArrowLeft,
  Activity,
  FlaskConical,
  Medal,
  ExternalLink,
  Hash,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Static params
// ---------------------------------------------------------------------------

export function generateStaticParams() {
  return getAllCategorySlugs().map((slug) => ({ slug }));
}

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  try {
    const detail = getCategoryDetail(slug);
    return {
      title: `${detail.category.name} | ModelRegression.com`,
      description: `Performance comparison of all models in the ${detail.category.name} category. ${detail.category.description}`,
    };
  } catch {
    return { title: "Category Not Found | ModelRegression.com" };
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getRankBadge(rank: number) {
  switch (rank) {
    case 1:
      return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
    case 2:
      return "bg-gray-400/15 text-gray-300 border-gray-400/30";
    case 3:
      return "bg-orange-700/15 text-orange-400 border-orange-700/30";
    default:
      return "bg-muted/50 text-muted-foreground border-border/50";
  }
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default async function CategoryDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  let detail;
  try {
    detail = getCategoryDetail(slug);
  } catch {
    notFound();
  }

  const { category, tests, models } = detail;
  const isTokenEfficiencyCategory =
    category.id === TOKEN_EFFICIENCY_CATEGORY_ID;

  // ---- Build line chart data from all models' history ----
  // Collect all unique timestamps
  const timestampSet = new Set<string>();
  for (const [, modelData] of Object.entries(models)) {
    for (const h of modelData.history) {
      timestampSet.add(h.timestamp);
    }
  }
  const allTimestamps = Array.from(timestampSet).sort();

  // Build lookup maps for fast access
  const modelHistoryMaps: Record<string, Map<string, number>> = {};
  for (const [modelId, modelData] of Object.entries(models)) {
    const map = new Map<string, number>();
    for (const h of modelData.history) {
      if (h.score != null) {
        map.set(h.timestamp, h.score);
      }
    }
    modelHistoryMaps[modelId] = map;
  }

  const chartData = allTimestamps.map((ts) => {
    const point: { timestamp: string; models: Record<string, number> } = {
      timestamp: ts,
      models: {},
    };
    for (const modelId of Object.keys(models)) {
      const val = modelHistoryMaps[modelId].get(ts);
      if (val !== undefined) {
        point.models[modelId] = val;
      }
    }
    return point;
  });

  // ---- Rank models by current score ----
  const rankedModels = Object.entries(models)
    .map(([modelId, data]) => ({
      modelId,
      info: getModel(modelId),
      score: data.currentScore,
      totalTokens: data.totalTokens,
      avgTokensPerTest: data.avgTokensPerTest,
      sparkline: data.history.slice(-7).map((h) => h.score ?? 0),
    }))
    .sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
    .map((m, i) => ({ ...m, rank: i + 1 }));

  // ---- Best average score across all models ----
  const scoredModels = rankedModels.filter((m) => m.score != null);
  const bestScore = scoredModels.length > 0 ? scoredModels[0].score ?? 0 : 0;
  const avgScore =
    scoredModels.length > 0
      ? scoredModels.reduce((sum, m) => sum + (m.score ?? 0), 0) /
        scoredModels.length
      : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* ----------------------------------------------------------------- */}
      {/* Back link                                                         */}
      {/* ----------------------------------------------------------------- */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* ----------------------------------------------------------------- */}
      {/* Category header                                                   */}
      {/* ----------------------------------------------------------------- */}
      <ScrollReveal>
        <div className="relative rounded-xl border border-border/50 glass p-6 md:p-8 overflow-hidden">
          {/* Decorative gradient */}
          <div className="absolute top-0 left-8 right-8 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
          <div className="absolute -top-32 -right-32 w-72 h-72 rounded-full bg-primary/5 blur-3xl pointer-events-none" />

          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between relative">
            {/* Left: Name + description */}
            <div className="space-y-3 max-w-2xl">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-full text-xs font-mono uppercase tracking-wider bg-muted/60 text-muted-foreground border border-border/50">
                  Category
                </span>
                <span className="text-xs font-mono text-muted-foreground">
                  Weight: {category.weight.toFixed(1)}x
                </span>
              </div>
              <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-foreground">
                {category.name}
              </h1>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {category.description}
              </p>
            </div>

            {/* Right: Stats */}
            <div className="grid w-full gap-3 sm:grid-cols-3 md:w-auto">
              <div className="rounded-xl border border-border/30 bg-background/25 p-4 text-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Best Score
                </p>
                <AnimatedCounter
                  value={bestScore}
                  className={cn(
                    "text-4xl font-extrabold",
                    getScoreColor(bestScore)
                  )}
                />
              </div>
              <div className="rounded-xl border border-border/30 bg-background/25 p-4 text-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Avg Score
                </p>
                <AnimatedCounter
                  value={avgScore}
                  className={cn(
                    "text-4xl font-extrabold",
                    getScoreColor(avgScore)
                  )}
                />
              </div>
              <div className="rounded-xl border border-border/30 bg-background/25 p-4 text-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  {isTokenEfficiencyCategory ? "Measured Models" : "Tests"}
                </p>
                <span className="text-4xl font-extrabold font-mono text-foreground">
                  {isTokenEfficiencyCategory ? scoredModels.length : tests.length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* ----------------------------------------------------------------- */}
      {/* All-models line chart                                             */}
      {/* ----------------------------------------------------------------- */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-5">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">
              Performance Over Time &mdash; All Models
            </h2>
          </div>
          <PerformanceLineChart
            data={chartData}
            height={400}
            showLegend={true}
          />
        </div>
      </ScrollReveal>

      {/* ----------------------------------------------------------------- */}
      {/* Model Ranking Table                                               */}
      {/* ----------------------------------------------------------------- */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass overflow-hidden">
          <div className="flex items-center gap-2 p-5 border-b border-border/50">
            <Medal className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">
              Model Rankings
            </h2>
          </div>
          <div className="grid gap-3 p-4 md:hidden">
            {rankedModels.map((rm) => {
              const info = rm.info;
              if (!info) return null;
              const delta = (rm.score ?? 0) - bestScore;

              return (
                <div
                  key={rm.modelId}
                  className="rounded-lg border border-border/40 bg-muted/10 p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={cn(
                          "inline-flex items-center justify-center h-7 w-7 rounded-lg border text-xs font-mono font-bold",
                          getRankBadge(rm.rank)
                        )}
                      >
                        {rm.rank}
                      </span>
                      <div>
                        <div
                          className="font-semibold text-sm"
                          style={{ color: info.color }}
                        >
                          {info.name}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {isTokenEfficiencyCategory ? "Token usage benchmark" : "Category score"}
                        </p>
                      </div>
                    </div>
                    <Link
                      href={`/models/${info.slug}`}
                      className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                    >
                      View
                      <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>

                  <div className="mt-4 flex items-center justify-between gap-3">
                    <span
                      className={cn(
                        "font-mono text-2xl font-bold",
                        getScoreColor(rm.score ?? 0)
                      )}
                    >
                      {formatScore(rm.score)}
                    </span>
                    <span
                      className={cn(
                        "font-mono text-xs font-medium",
                        delta === 0 ? "text-yellow-400" : "text-muted-foreground"
                      )}
                    >
                      {delta === 0 ? "BEST" : `${delta.toFixed(1)} pts`}
                    </span>
                  </div>

                  <div className="mt-3 rounded-lg border border-border/30 bg-background/25 p-3">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{isTokenEfficiencyCategory ? "Avg/Test" : "Tokens"}</span>
                      <span className="font-mono text-foreground">
                        {isTokenEfficiencyCategory
                          ? formatTokens(rm.avgTokensPerTest)
                          : formatTokens(rm.totalTokens)}
                        {isTokenEfficiencyCategory ? "/test" : ""}
                      </span>
                    </div>
                    {rm.totalTokens != null && (
                      <div className="mt-1 flex items-center justify-between text-[11px] text-muted-foreground/80">
                        <span>Total</span>
                        <span className="font-mono">{formatTokens(rm.totalTokens)}</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-3 rounded-lg border border-border/30 bg-background/25 p-2">
                    <Sparkline
                      data={rm.sparkline.map((value) => value ?? 0)}
                      color={info.color}
                      width={240}
                      height={28}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="hidden overflow-x-auto md:block">
            <table className="w-full min-w-[580px]">
              <thead>
                <tr className="border-b border-border/30">
                  <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-5">
                    Rank
                  </th>
                  <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-4">
                    Model
                  </th>
                  <th className="text-center text-[11px] font-medium text-muted-foreground py-3 px-4">
                    Score
                  </th>
                  <th className="text-center text-[11px] font-medium text-muted-foreground py-3 px-4">
                    7-Day Trend
                  </th>
                  <th className="text-center text-[11px] font-medium text-muted-foreground py-3 px-4">
                    {isTokenEfficiencyCategory ? "Avg/Test" : "Tokens"}
                  </th>
                  <th className="text-center text-[11px] font-medium text-muted-foreground py-3 px-4">
                    vs. Best
                  </th>
                  <th className="text-right text-[11px] font-medium text-muted-foreground py-3 px-5">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody>
                  {rankedModels.map((rm) => {
                    const info = rm.info;
                    if (!info) return null;
                  const delta = (rm.score ?? 0) - bestScore;

                  return (
                    <tr
                      key={rm.modelId}
                      className="border-b border-border/20 hover:bg-muted/20 transition-colors"
                    >
                      <td className="py-3 px-5">
                        <span
                          className={cn(
                            "inline-flex items-center justify-center w-7 h-7 rounded-lg text-xs font-mono font-bold border",
                            getRankBadge(rm.rank)
                          )}
                        >
                          {rm.rank}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2.5">
                          <div
                            className="w-2.5 h-2.5 rounded-full"
                            style={{ backgroundColor: info.color }}
                          />
                          <span
                            className="font-medium text-sm"
                            style={{ color: info.color }}
                          >
                            {info.name}
                          </span>
                        </div>
                      </td>
                      <td className="text-center py-3 px-4">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
                            <div
                              className="h-full rounded-full score-bar"
                              style={{
                                width: `${rm.score ?? 0}%`,
                                backgroundColor: info.color,
                              }}
                            />
                          </div>
                          <span
                            className={cn(
                              "font-mono font-bold text-sm",
                              getScoreColor(rm.score)
                            )}
                          >
                            {formatScore(rm.score)}
                          </span>
                        </div>
                      </td>
                      <td className="text-center py-3 px-4">
                        <div className="flex justify-center">
                          <Sparkline
                            data={rm.sparkline}
                            color={info.color}
                            width={80}
                            height={28}
                          />
                        </div>
                      </td>
                      <td className="text-center py-3 px-4">
                        <span className="font-mono text-xs text-muted-foreground">
                          {isTokenEfficiencyCategory
                            ? `${formatTokens(rm.avgTokensPerTest)}/test`
                            : formatTokens(rm.totalTokens)}
                        </span>
                      </td>
                      <td className="text-center py-3 px-4">
                        <span
                          className={cn(
                            "font-mono text-xs font-medium",
                            delta === 0
                              ? "text-yellow-400"
                              : "text-muted-foreground"
                          )}
                        >
                          {delta === 0
                            ? "BEST"
                            : `${delta.toFixed(1)} pts`}
                        </span>
                      </td>
                      <td className="text-right py-3 px-5">
                        <Link
                          href={`/models/${info.slug}`}
                          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                        >
                          View
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </ScrollReveal>

      {/* ----------------------------------------------------------------- */}
      {/* Individual Test Breakdown                                         */}
      {/* ----------------------------------------------------------------- */}
      <ScrollReveal>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">
              {isTokenEfficiencyCategory ? "Benchmark Construction" : "Test Breakdown"}
            </h2>
          </div>

          {isTokenEfficiencyCategory ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border/50 glass p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Hash className="w-4 h-4 text-blue-400" />
                  <h3 className="text-sm font-semibold text-foreground">
                    How It Scores
                  </h3>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">
                  We total prompt and completion tokens across all successful
                  benchmark tasks, compute an average per successful task, then
                  assign 100 to the lowest-burn model in that run. Everyone else
                  is scaled down proportionally, so higher usage means a lower
                  benchmark score.
                </p>
              </div>
              <div className="rounded-xl border border-border/50 glass p-5">
                <h3 className="text-sm font-semibold text-foreground mb-3">
                  What To Read In This View
                </h3>
                <div className="space-y-3 text-sm text-muted-foreground">
                  <p>
                    The ranking table above is the benchmark itself. Use
                    <span className="font-mono text-foreground"> Avg/Test </span>
                    to compare per-task burn and
                    <span className="font-mono text-foreground"> Total </span>
                    to spot larger absolute usage across the whole run.
                  </p>
                  <p>
                    Historical scores show whether a model is becoming more or
                    less token-efficient over time, independent of raw quality
                    improvements in the other ten categories.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {tests.map((test) => (
                <div
                  key={test.id}
                  className="rounded-xl border border-border/50 glass p-5"
                >
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-foreground">
                      {test.name}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {test.description}
                    </p>
                  </div>

                  {/* Per-model bars for this test -- rendered from ranked data */}
                  <div className="space-y-2.5">
                    {rankedModels.map((rm) => {
                      const info = rm.info;
                      if (!info) return null;

                      // We don't have per-test per-model scores in the
                      // category detail data. Use the model's overall
                      // category score as a proxy.
                      const score = rm.score ?? 0;

                      return (
                        <div key={rm.modelId} className="space-y-1">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <div
                                className="w-2 h-2 rounded-full"
                                style={{ backgroundColor: info.color }}
                              />
                              <span
                                className="text-xs font-medium"
                                style={{ color: info.color }}
                              >
                                {info.name}
                              </span>
                            </div>
                            <span
                              className={cn(
                                "font-mono text-xs font-bold",
                                getScoreColor(score)
                              )}
                            >
                              {formatScore(score)}
                            </span>
                          </div>
                          <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
                            <div
                              className="h-full rounded-full score-bar"
                              style={{
                                width: `${score}%`,
                                backgroundColor: info.color,
                                opacity: 0.85,
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </ScrollReveal>
    </div>
  );
}
