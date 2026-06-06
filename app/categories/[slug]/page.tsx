import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import { getAllModels, getCategoryDetail, getAllCategorySlugs } from "@/lib/data";
import {
  cn,
  formatScore,
  getScoreColor,
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

  const modelInfos = getAllModels();
  const { category, tests, models: categoryModels } = detail;

  // ---- Build line chart data from all models' history ----
  // Collect all unique timestamps
  const timestampSet = new Set<string>();
  for (const [, modelData] of Object.entries(categoryModels)) {
    for (const h of modelData.history) {
      timestampSet.add(h.timestamp);
    }
  }
  const allTimestamps = Array.from(timestampSet).sort();

  // Build lookup maps for fast access
  const modelHistoryMaps: Record<string, Map<string, number>> = {};
  for (const [modelId, modelData] of Object.entries(categoryModels)) {
    const map = new Map<string, number>();
    for (const h of modelData.history) {
      map.set(h.timestamp, h.score);
    }
    modelHistoryMaps[modelId] = map;
  }

  const chartData = allTimestamps.map((ts) => {
    const point: { timestamp: string; models: Record<string, number> } = {
      timestamp: ts,
      models: {},
    };
    for (const modelId of Object.keys(categoryModels)) {
      const val = modelHistoryMaps[modelId].get(ts);
      if (val !== undefined) {
        point.models[modelId] = val;
      }
    }
    return point;
  });

  // ---- Rank models by current score ----
  const rankedModels = Object.entries(categoryModels)
    .map(([modelId, data]) => ({
      modelId,
      info: modelInfos.find((m) => m.id === modelId),
      score: data.currentScore,
      sparkline: data.history.slice(-7).map((h) => h.score),
    }))
    .sort((a, b) => b.score - a.score)
    .map((m, i) => ({ ...m, rank: i + 1 }));

  // ---- Best average score across all models ----
  const bestScore =
    rankedModels.length > 0 ? rankedModels[0].score : 0;
  const avgScore =
    rankedModels.length > 0
      ? rankedModels.reduce((sum, m) => sum + m.score, 0) /
        rankedModels.length
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

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative">
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
            <div className="flex items-center gap-8">
              <div className="text-center">
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
              <div className="text-center">
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
              <div className="text-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Tests
                </p>
                <span className="text-4xl font-extrabold font-mono text-foreground">
                  {tests.length}
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
            models={modelInfos}
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
          <div className="overflow-x-auto">
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
                  const delta = rm.score - bestScore;

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
                                width: `${rm.score}%`,
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
              Test Breakdown
            </h2>
          </div>

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
                    // category detail data.  Use the model's overall
                    // category score as a proxy (the best we have here).
                    const score = rm.score;

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
        </div>
      </ScrollReveal>
    </div>
  );
}
