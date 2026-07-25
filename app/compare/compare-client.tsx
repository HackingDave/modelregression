"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { MODELS } from "@/lib/models";
import { CATEGORIES, TOKEN_EFFICIENCY_CATEGORY_ID } from "@/lib/categories";
import { formatScore, getScoreColor, formatTokens } from "@/lib/utils";
import { CategoryRadarChart } from "@/components/charts/category-radar-chart";
import { PerformanceLineChart } from "@/components/charts/performance-line-chart";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import { Check } from "lucide-react";
import type { TrendData, LatestRun } from "@/lib/types";

interface CompareClientProps {
  scores: Record<string, Record<string, number | null>>;
  trends: TrendData;
  latest: LatestRun;
}

export function CompareClient({ scores, trends, latest }: CompareClientProps) {
  const availableModelIds = MODELS.filter(
    (model) => latest.models[model.id]?.compositeScore != null
  ).map((model) => model.id);
  const [selected, setSelected] = useState<string[]>(
    availableModelIds
  );
  const selectedModels = MODELS.filter((m) => selected.includes(m.id));
  const metricCards = [
    {
      id: "composite",
      label: "Composite",
      getValue: (modelId: string) => latest.models[modelId]?.compositeScore ?? null,
      renderValue: (modelId: string) =>
        formatScore(latest.models[modelId]?.compositeScore ?? null),
      getClassName: (modelId: string) =>
        getScoreColor(latest.models[modelId]?.compositeScore ?? null),
    },
    {
      id: "token-benchmark",
      label: "Token Benchmark",
      getValue: (modelId: string) =>
        latest.models[modelId]?.categories[TOKEN_EFFICIENCY_CATEGORY_ID]?.avgScore ?? null,
      renderValue: (modelId: string) =>
        formatScore(
          latest.models[modelId]?.categories[TOKEN_EFFICIENCY_CATEGORY_ID]?.avgScore ?? null
        ),
      getClassName: (modelId: string) =>
        getScoreColor(
          latest.models[modelId]?.categories[TOKEN_EFFICIENCY_CATEGORY_ID]?.avgScore ?? null
        ),
    },
    {
      id: "avg-tokens",
      label: "Avg Tokens/Test",
      getValue: (modelId: string) => latest.models[modelId]?.avgTokensPerTest ?? null,
      renderValue: (modelId: string) => formatTokens(latest.models[modelId]?.avgTokensPerTest),
      getClassName: () => "text-blue-400",
    },
    {
      id: "total-tokens",
      label: "Total Tokens",
      getValue: (modelId: string) => latest.models[modelId]?.totalTokens ?? null,
      renderValue: (modelId: string) => formatTokens(latest.models[modelId]?.totalTokens),
      getClassName: () => "text-muted-foreground",
    },
  ];

  const toggle = (id: string) => {
    if (!availableModelIds.includes(id)) return;
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const filteredScores: Record<string, Record<string, number | null>> = {};
  for (const id of selected) {
    filteredScores[id] = scores[id] ?? {};
  }

  return (
    <div className="space-y-8">
      {/* Model selector */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-5">
          <h3 className="text-sm font-semibold text-foreground mb-3">
            Select Models to Compare
          </h3>
          <div className="flex flex-wrap gap-2">
            {MODELS.map((model) => {
              const isSelected = selected.includes(model.id);
              const isAvailable = availableModelIds.includes(model.id);
              return (
                <button
                  key={model.id}
                  onClick={() => toggle(model.id)}
                  disabled={!isAvailable}
                  aria-pressed={isSelected}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-all",
                    !isAvailable && "cursor-not-allowed opacity-50",
                    isSelected
                      ? "border-opacity-60 bg-opacity-10"
                      : "border-border/50 bg-transparent text-muted-foreground hover:bg-muted/30"
                  )}
                  style={{
                    borderColor: isSelected ? model.color : undefined,
                    backgroundColor: isSelected
                      ? `${model.color}15`
                      : undefined,
                    color: isSelected ? model.color : undefined,
                  }}
                >
                  {isSelected && <Check className="w-3.5 h-3.5" />}
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: model.color }}
                  />
                  {model.name}
                  {!isAvailable && (
                    <span className="text-[10px] font-normal text-muted-foreground">
                      Awaiting run
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </ScrollReveal>

      {selected.length === 0 && (
        <div className="rounded-xl border border-dashed border-border/60 bg-muted/10 p-8 text-center">
          <h3 className="text-sm font-semibold text-foreground">
            Select at least one model
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Choose a model with benchmark data to display its scores and trends.
          </p>
        </div>
      )}

      {/* Radar Chart */}
      {selected.length > 0 && (
        <ScrollReveal>
          <div className="rounded-xl border border-border/50 glass p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">
              Category Radar Comparison
            </h3>
            <div className="rounded-lg border border-border/30 bg-background/20 p-4 md:hidden">
              <p className="text-sm text-muted-foreground leading-6">
                The radar visualization is shown on wider screens. On mobile,
                use the detailed comparison cards below for exact per-category,
                composite, and token-efficiency values without clipped labels.
              </p>
            </div>
            <div className="hidden md:block">
              <CategoryRadarChart
                scores={filteredScores}
                modelFilter={selected}
                height={450}
              />
            </div>
          </div>
        </ScrollReveal>
      )}

      {/* Performance Timeline */}
      {selected.length > 0 && (
        <ScrollReveal>
          <div className="rounded-xl border border-border/50 glass p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">
              Performance Over Time
            </h3>
            <PerformanceLineChart
              data={trends.data}
              modelFilter={selected}
              height={350}
            />
          </div>
        </ScrollReveal>
      )}

      {/* Comparison Table */}
      {selected.length > 0 && (
        <ScrollReveal>
          <div className="rounded-xl border border-border/50 glass overflow-hidden">
            <div className="p-5 border-b border-border/50">
              <h3 className="text-sm font-semibold text-foreground">
                Detailed Score Comparison
              </h3>
            </div>
            <div className="space-y-3 p-4 md:hidden">
              {metricCards.map((metric) => (
                <div
                  key={metric.id}
                  className="rounded-lg border border-border/40 bg-muted/10 p-4"
                >
                  <h4 className="text-sm font-semibold text-foreground">
                    {metric.label}
                  </h4>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {selectedModels.map((model) => (
                      <div
                        key={`${metric.id}-${model.id}`}
                        className="rounded-md border border-border/30 bg-background/25 px-3 py-2"
                      >
                        <p
                          className="text-[11px] font-medium"
                          style={{ color: model.color }}
                        >
                          {model.name}
                        </p>
                        <p
                          className={cn(
                            "mt-1 font-mono text-sm font-semibold",
                            metric.getClassName(model.id)
                          )}
                        >
                          {metric.renderValue(model.id)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {CATEGORIES.map((cat) => {
                const categoryScores = selectedModels
                  .map((model) => scores[model.id]?.[cat.id] ?? null)
                  .filter((score): score is number => score != null);
                const bestScore = categoryScores.length
                  ? Math.max(...categoryScores)
                  : null;

                return (
                  <div
                    key={cat.id}
                    className="rounded-lg border border-border/40 bg-muted/10 p-4"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-semibold text-foreground">
                        {cat.name}
                      </span>
                      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                        Category
                      </span>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      {selectedModels.map((model) => {
                        const score = scores[model.id]?.[cat.id] ?? null;
                        const isBest =
                          score != null && bestScore != null && score === bestScore;

                        return (
                          <div
                            key={`${cat.id}-${model.id}`}
                            className="rounded-md border border-border/30 bg-background/25 px-3 py-2"
                          >
                            <p
                              className="text-[11px] font-medium"
                              style={{ color: model.color }}
                            >
                              {model.name}
                            </p>
                            <p
                              className={cn(
                                "mt-1 font-mono text-sm font-semibold",
                                getScoreColor(score)
                              )}
                            >
                              {formatScore(score)}
                              {isBest ? (
                                <span className="ml-1 text-[10px] text-yellow-400">
                                  BEST
                                </span>
                              ) : null}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full min-w-[680px]">
                <thead>
                  <tr className="border-b border-border/30">
                    <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-4 w-44">
                      Category
                    </th>
                    {selectedModels.map((model) => (
                      <th
                        key={model.id}
                        className="text-center text-[11px] font-medium py-3 px-3"
                        style={{ color: model.color }}
                      >
                        {model.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {CATEGORIES.map((cat) => {
                    const catScores = selectedModels
                      .map((m) => scores[m.id]?.[cat.id] ?? null)
                      .filter((score): score is number => score != null);
                    const maxScore = catScores.length
                      ? Math.max(...catScores)
                      : null;

                    return (
                      <tr
                        key={cat.id}
                        className="border-b border-border/20 hover:bg-muted/10"
                      >
                        <td className="py-3 px-4 text-sm text-muted-foreground">
                          {cat.name}
                        </td>
                        {selectedModels.map((model) => {
                          const score = scores[model.id]?.[cat.id] ?? null;
                          const isBest =
                            score != null && maxScore != null && score === maxScore;
                          return (
                            <td key={model.id} className="text-center py-3 px-3">
                              <span
                                className={cn(
                                  "font-mono text-sm font-medium",
                                  getScoreColor(score),
                                  isBest && "underline decoration-2 underline-offset-2"
                                )}
                                style={{
                                  textDecorationColor: isBest
                                    ? model.color
                                    : undefined,
                                }}
                              >
                                {formatScore(score)}
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}

                  {/* Composite row */}
                  <tr className="bg-muted/10">
                    <td className="py-3 px-4 text-sm font-semibold text-foreground">
                      Composite
                    </td>
                    {selectedModels.map((model) => {
                      const result = latest.models[model.id];
                      return (
                        <td
                          key={model.id}
                          className="text-center py-3 px-3"
                        >
                          <span
                            className={cn(
                              "font-mono text-sm font-bold",
                              getScoreColor(
                                result?.compositeScore ?? null
                              )
                            )}
                          >
                            {formatScore(
                              result?.compositeScore ?? null
                            )}
                          </span>
                        </td>
                      );
                    })}
                  </tr>

                  {/* Total Tokens row */}
                  <tr className="bg-muted/5">
                    <td className="py-3 px-4 text-sm font-semibold text-foreground">
                      Total Tokens
                    </td>
                    {selectedModels.map((model) => {
                      const result = latest.models[model.id];
                      return (
                        <td
                          key={model.id}
                          className="text-center py-3 px-3"
                        >
                          <span className="font-mono text-sm text-muted-foreground">
                            {formatTokens(result?.totalTokens)}
                          </span>
                        </td>
                      );
                    })}
                  </tr>

                  {/* Avg tokens per test row */}
                  <tr className="bg-muted/5">
                    <td className="py-3 px-4 text-sm font-semibold text-foreground">
                      Avg Tokens / Test
                    </td>
                    {selectedModels.map((model) => {
                      const result = latest.models[model.id];
                      return (
                        <td
                          key={model.id}
                          className="text-center py-3 px-3"
                        >
                          <span className="font-mono text-sm text-blue-400">
                            {formatTokens(result?.avgTokensPerTest)}
                          </span>
                        </td>
                      );
                    })}
                  </tr>

                  {/* Token benchmark row */}
                  <tr className="bg-muted/10">
                    <td className="py-3 px-4 text-sm font-semibold text-foreground">
                      Token Benchmark
                    </td>
                    {selectedModels.map((model) => {
                      const result = latest.models[model.id];
                      const tokenBenchmark =
                        result?.categories[TOKEN_EFFICIENCY_CATEGORY_ID]?.avgScore ?? null;

                      return (
                        <td
                          key={model.id}
                          className="text-center py-3 px-3"
                        >
                          <span
                            className={cn(
                              "font-mono text-sm font-bold",
                              getScoreColor(tokenBenchmark)
                            )}
                          >
                            {formatScore(tokenBenchmark)}
                          </span>
                        </td>
                      );
                    })}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </ScrollReveal>
      )}
    </div>
  );
}
