"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { MODELS } from "@/lib/models";
import { CATEGORIES } from "@/lib/categories";
import { formatScore, getScoreColor } from "@/lib/utils";
import { CategoryRadarChart } from "@/components/charts/category-radar-chart";
import { PerformanceLineChart } from "@/components/charts/performance-line-chart";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import { Check } from "lucide-react";
import type { TrendData, LatestRun } from "@/lib/types";

interface CompareClientProps {
  scores: Record<string, Record<string, number>>;
  trends: TrendData;
  latest: LatestRun;
}

export function CompareClient({ scores, trends, latest }: CompareClientProps) {
  const [selected, setSelected] = useState<string[]>(
    MODELS.map((m) => m.id)
  );

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const filteredScores: Record<string, Record<string, number>> = {};
  for (const id of selected) {
    filteredScores[id] = scores[id];
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
              return (
                <button
                  key={model.id}
                  onClick={() => toggle(model.id)}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-all",
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
                </button>
              );
            })}
          </div>
        </div>
      </ScrollReveal>

      {/* Radar Chart */}
      {selected.length > 0 && (
        <ScrollReveal>
          <div className="rounded-xl border border-border/50 glass p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">
              Category Radar Comparison
            </h3>
            <CategoryRadarChart
              scores={filteredScores}
              modelFilter={selected}
              height={450}
            />
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
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border/30">
                    <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-4 w-44">
                      Category
                    </th>
                    {MODELS.filter((m) => selected.includes(m.id)).map(
                      (model) => (
                        <th
                          key={model.id}
                          className="text-center text-[11px] font-medium py-3 px-3"
                          style={{ color: model.color }}
                        >
                          {model.name}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody>
                  {CATEGORIES.map((cat) => {
                    const selectedModels = MODELS.filter((m) =>
                      selected.includes(m.id)
                    );
                    const catScores = selectedModels.map(
                      (m) => scores[m.id]?.[cat.id] ?? 0
                    );
                    const maxScore = Math.max(...catScores);

                    return (
                      <tr
                        key={cat.id}
                        className="border-b border-border/20 hover:bg-muted/10"
                      >
                        <td className="py-3 px-4 text-sm text-muted-foreground">
                          {cat.name}
                        </td>
                        {selectedModels.map((model) => {
                          const score = scores[model.id]?.[cat.id] ?? 0;
                          const isBest = score === maxScore && score > 0;
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
                    {MODELS.filter((m) => selected.includes(m.id)).map(
                      (model) => {
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
                                  result?.compositeScore ?? 0
                                )
                              )}
                            >
                              {formatScore(
                                result?.compositeScore ?? 0
                              )}
                            </span>
                          </td>
                        );
                      }
                    )}
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
