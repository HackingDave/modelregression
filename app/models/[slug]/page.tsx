import { notFound } from "next/navigation";
import Link from "next/link";
import type { Metadata } from "next";
import { getModelDetail, getAllModelSlugs } from "@/lib/data";
import { getProviderName } from "@/lib/models";
import { CATEGORIES } from "@/lib/categories";
import {
  cn,
  formatScore,
  formatPercent,
  getScoreColor,
  formatDate,
  formatDateTime,
  formatDuration,
} from "@/lib/utils";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import { AnimatedCounter } from "@/components/shared/animated-counter";
import { CategoryRadarChart } from "@/components/charts/category-radar-chart";
import { PerformanceLineChart } from "@/components/charts/performance-line-chart";
import { Sparkline } from "@/components/charts/sparkline";
import {
  ArrowLeft,
  Trophy,
  TrendingDown,
  Clock,
  Zap,
  BarChart3,
  Activity,
  Shield,
  XCircle,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Static params
// ---------------------------------------------------------------------------

export function generateStaticParams() {
  return getAllModelSlugs().map((slug) => ({ slug }));
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
    const detail = getModelDetail(slug);
    return {
      title: `${detail.model.name} Performance | ModelRegression.com`,
      description: `Detailed benchmark results, regression history, and performance trends for ${detail.model.name}.`,
    };
  } catch {
    return { title: "Model Not Found | ModelRegression.com" };
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getSeverityBadge(severity: string) {
  switch (severity) {
    case "major":
      return "bg-red-500/15 text-red-400 border-red-500/30";
    case "moderate":
      return "bg-orange-500/15 text-orange-400 border-orange-500/30";
    default:
      return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
  }
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default async function ModelDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  let detail;
  try {
    detail = getModelDetail(slug);
  } catch {
    notFound();
  }

  const { model, current, history, regressions, outages } = detail;

  // ---- Radar chart scores: this model across all categories ----
  const radarScores: Record<string, Record<string, number>> = {
    [model.id]: {},
  };
  for (const cat of CATEGORIES) {
    radarScores[model.id][cat.id] =
      current.categories[cat.id]?.avgScore ?? 0;
  }

  // ---- Line chart data: composite score history ----
  const lineChartData = history.map((h) => ({
    timestamp: h.timestamp,
    models: { [model.id]: h.compositeScore },
  }));

  // ---- Sparkline per category from history (last 7 entries) ----
  const categorySparklines: Record<string, number[]> = {};
  for (const cat of CATEGORIES) {
    categorySparklines[cat.id] = history.slice(-7).map(
      (h) => h.categories[cat.id] ?? 0
    );
  }

  // ---- Sorted categories by score (descending) ----
  const sortedCategories = CATEGORIES.map((cat) => ({
    ...cat,
    score: current.categories[cat.id]?.avgScore ?? 0,
  })).sort((a, b) => b.score - a.score);

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
      {/* Model header                                                      */}
      {/* ----------------------------------------------------------------- */}
      <ScrollReveal>
        <div className="relative rounded-xl border border-border/50 glass p-6 md:p-8 overflow-hidden">
          {/* Top glow accent */}
          <div
            className="absolute top-0 left-8 right-8 h-px"
            style={{
              background: `linear-gradient(90deg, transparent, ${model.color}60, transparent)`,
            }}
          />
          {/* Decorative orb */}
          <div
            className="absolute -top-24 -right-24 w-64 h-64 rounded-full opacity-10 blur-3xl pointer-events-none"
            style={{ backgroundColor: model.color }}
          />

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative">
            {/* Left: Provider badge + model name */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: model.color }}
                />
                <span className="px-2.5 py-1 rounded-full text-xs font-mono uppercase tracking-wider bg-muted/60 text-muted-foreground border border-border/50">
                  {getProviderName(model.provider)}
                </span>
              </div>
              <h1
                className="text-3xl md:text-4xl font-extrabold tracking-tight"
                style={{ color: model.color }}
              >
                {model.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                Comprehensive benchmark performance across {CATEGORIES.length}{" "}
                evaluation categories
              </p>
            </div>

            {/* Right: Score + Rank */}
            <div className="flex items-center gap-8">
              <div className="text-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Composite Score
                </p>
                <AnimatedCounter
                  value={current.compositeScore}
                  className={cn(
                    "text-5xl font-extrabold",
                    getScoreColor(current.compositeScore)
                  )}
                />
                <span className="text-lg text-muted-foreground font-mono">
                  /100
                </span>
              </div>
              <div className="text-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">
                  Rank
                </p>
                <div className="flex items-center gap-1.5">
                  <Trophy className="w-6 h-6 text-yellow-500" />
                  <span className="text-5xl font-extrabold font-mono text-foreground">
                    #{current.rank}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* ----------------------------------------------------------------- */}
      {/* Charts row: Radar + Line                                          */}
      {/* ----------------------------------------------------------------- */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Radar */}
        <ScrollReveal>
          <div className="rounded-xl border border-border/50 glass p-5">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-4 h-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">
                Category Radar
              </h2>
            </div>
            <CategoryRadarChart
              scores={radarScores}
              modelFilter={[model.id]}
              height={380}
            />
          </div>
        </ScrollReveal>

        {/* Line chart */}
        <ScrollReveal delay={0.1}>
          <div className="rounded-xl border border-border/50 glass p-5">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-4 h-4 text-muted-foreground" />
              <h2 className="text-sm font-semibold text-foreground">
                Historical Composite Score
              </h2>
            </div>
            <PerformanceLineChart
              data={lineChartData}
              modelFilter={[model.id]}
              height={380}
              showLegend={false}
            />
          </div>
        </ScrollReveal>
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* Category Breakdown Table                                          */}
      {/* ----------------------------------------------------------------- */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass overflow-hidden">
          <div className="flex items-center gap-2 p-5 border-b border-border/50">
            <Shield className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">
              Category Breakdown
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px]">
              <thead>
                <tr className="border-b border-border/30">
                  <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-5">
                    #
                  </th>
                  <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-4">
                    Category
                  </th>
                  <th className="text-center text-[11px] font-medium text-muted-foreground py-3 px-4">
                    Score
                  </th>
                  <th className="text-center text-[11px] font-medium text-muted-foreground py-3 px-4">
                    Tests
                  </th>
                  <th className="text-center text-[11px] font-medium text-muted-foreground py-3 px-4">
                    7-Day Trend
                  </th>
                  <th className="text-right text-[11px] font-medium text-muted-foreground py-3 px-5">
                    Weight
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedCategories.map((cat, idx) => {
                  const catScore = current.categories[cat.id];
                  return (
                    <tr
                      key={cat.id}
                      className="border-b border-border/20 hover:bg-muted/20 transition-colors"
                    >
                      <td className="py-3 px-5 text-xs font-mono text-muted-foreground">
                        {idx + 1}
                      </td>
                      <td className="py-3 px-4">
                        <Link
                          href={`/categories/${cat.slug}`}
                          className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                        >
                          {cat.name}
                        </Link>
                      </td>
                      <td className="text-center py-3 px-4">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden">
                            <div
                              className="h-full rounded-full score-bar"
                              style={{
                                width: `${cat.score}%`,
                                backgroundColor: model.color,
                              }}
                            />
                          </div>
                          <span
                            className={cn(
                              "font-mono font-bold text-sm",
                              getScoreColor(cat.score)
                            )}
                          >
                            {formatScore(cat.score)}
                          </span>
                        </div>
                      </td>
                      <td className="text-center py-3 px-4 text-xs font-mono text-muted-foreground">
                        {catScore?.testCount ?? 0}
                      </td>
                      <td className="text-center py-3 px-4">
                        <div className="flex justify-center">
                          <Sparkline
                            data={categorySparklines[cat.id]}
                            color={model.color}
                            width={80}
                            height={28}
                          />
                        </div>
                      </td>
                      <td className="text-right py-3 px-5 text-xs font-mono text-muted-foreground">
                        {cat.weight.toFixed(1)}x
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
      {/* Individual Test Results (grouped by category)                     */}
      {/* ----------------------------------------------------------------- */}
      <ScrollReveal>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-foreground">
              Individual Test Results
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {CATEGORIES.map((cat) => {
              const catScore = current.categories[cat.id];
              if (!catScore) return null;

              return (
                <div
                  key={cat.id}
                  className="rounded-xl border border-border/50 glass p-5"
                >
                  <div className="flex items-center justify-between mb-4">
                    <Link
                      href={`/categories/${cat.slug}`}
                      className="text-sm font-semibold text-foreground hover:text-primary transition-colors"
                    >
                      {cat.name}
                    </Link>
                    <span
                      className={cn(
                        "font-mono font-bold text-sm",
                        getScoreColor(catScore.avgScore)
                      )}
                    >
                      {formatScore(catScore.avgScore)}
                    </span>
                  </div>

                  <div className="space-y-3">
                    {catScore.tests.map((test) => (
                      <div key={test.testId} className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-muted-foreground truncate pr-2">
                            {test.name}
                          </span>
                          <div className="flex items-center gap-3 flex-shrink-0">
                            <span className="text-[10px] font-mono text-muted-foreground/70">
                              {formatDuration(test.latencyMs)}
                            </span>
                            <span
                              className={cn(
                                "font-mono text-xs font-bold",
                                getScoreColor(test.score)
                              )}
                            >
                              {formatScore(test.score)}
                            </span>
                          </div>
                        </div>
                        <div className="w-full h-1 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full score-bar"
                            style={{
                              width: `${test.score}%`,
                              backgroundColor: model.color,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </ScrollReveal>

      {/* ----------------------------------------------------------------- */}
      {/* Regression History                                                */}
      {/* ----------------------------------------------------------------- */}
      {regressions.length > 0 && (
        <ScrollReveal>
          <div className="rounded-xl border border-border/50 glass overflow-hidden">
            <div className="flex items-center gap-2 p-5 border-b border-border/50">
              <TrendingDown className="w-4 h-4 text-orange-400" />
              <h2 className="text-sm font-semibold text-foreground">
                Regression History
              </h2>
              <span className="px-2 py-0.5 rounded-full text-xs font-mono bg-red-500/10 text-red-400 border border-red-500/20">
                {regressions.length}
              </span>
            </div>

            <div className="divide-y divide-border/20">
              {regressions.map((reg) => {
                const isResolved = reg.resolvedAt !== null;
                return (
                  <div
                    key={reg.id}
                    className="flex items-start gap-4 p-5 hover:bg-muted/10 transition-colors"
                  >
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full mt-1.5 flex-shrink-0",
                        isResolved ? "bg-green-500" : "bg-red-500 animate-pulse"
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-foreground">
                          {reg.categoryName || "Overall Composite"}
                        </span>
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-medium border",
                            getSeverityBadge(reg.severity)
                          )}
                        >
                          {reg.severity}
                        </span>
                        {isResolved && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-medium bg-green-500/15 text-green-400 border border-green-500/30">
                            resolved
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Score dropped{" "}
                        <span className="font-mono text-red-400">
                          {formatPercent(reg.dropPct)}
                        </span>{" "}
                        from{" "}
                        <span className="font-mono">
                          {formatScore(reg.previousAvg)}
                        </span>{" "}
                        to{" "}
                        <span className="font-mono">
                          {formatScore(reg.currentScore)}
                        </span>
                      </p>
                      <div className="flex items-center gap-3 mt-1.5 text-[10px] text-muted-foreground/70">
                        <span>
                          Detected {formatDate(reg.detectedAt)}
                        </span>
                        <span>&middot;</span>
                        <span>{reg.windowDays}-day window</span>
                        {isResolved && reg.resolvedAt && (
                          <>
                            <span>&middot;</span>
                            <span>
                              Resolved {formatDate(reg.resolvedAt)}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </ScrollReveal>
      )}

      {/* ----------------------------------------------------------------- */}
      {/* Outage History                                                    */}
      {/* ----------------------------------------------------------------- */}
      {outages.length > 0 && (
        <ScrollReveal>
          <div className="rounded-xl border border-border/50 glass overflow-hidden">
            <div className="flex items-center gap-2 p-5 border-b border-border/50">
              <XCircle className="w-4 h-4 text-red-400" />
              <h2 className="text-sm font-semibold text-foreground">
                Outage History
              </h2>
              <span className="px-2 py-0.5 rounded-full text-xs font-mono bg-red-500/10 text-red-400 border border-red-500/20">
                {outages.length}
              </span>
            </div>

            <div className="divide-y divide-border/20">
              {outages.map((outage) => {
                const isOngoing = outage.endedAt === null;
                return (
                  <div
                    key={outage.id}
                    className="flex items-start gap-4 p-5 hover:bg-muted/10 transition-colors"
                  >
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full mt-1.5 flex-shrink-0",
                        isOngoing
                          ? "bg-red-500 animate-pulse"
                          : "bg-muted-foreground"
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className="text-sm font-semibold text-foreground">
                          {outage.errorType}
                        </span>
                        {outage.httpStatus && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-red-500/15 text-red-400 border border-red-500/30">
                            HTTP {outage.httpStatus}
                          </span>
                        )}
                        {isOngoing && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-medium bg-red-500/15 text-red-400 border border-red-500/30">
                            ongoing
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground truncate">
                        {outage.errorMessage}
                      </p>
                      <div className="flex items-center gap-3 mt-1.5 text-[10px] text-muted-foreground/70">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Started {formatDateTime(outage.startedAt)}
                        </span>
                        {outage.endedAt && (
                          <>
                            <span>&middot;</span>
                            <span>
                              Ended {formatDateTime(outage.endedAt)}
                            </span>
                          </>
                        )}
                        <span>&middot;</span>
                        <span>
                          {outage.checkCount} check
                          {outage.checkCount !== 1 ? "s" : ""} affected
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </ScrollReveal>
      )}
    </div>
  );
}
