"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { formatScore, getScoreColor, formatDateTime } from "@/lib/utils";
import { CATEGORIES } from "@/lib/categories";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import { Clock, ExternalLink } from "lucide-react";
import type { LatestRun, ModelInfo } from "@/lib/types";

interface LatestRunTableProps {
  run: LatestRun;
  models: ModelInfo[];
}

export function LatestRunTable({ run, models }: LatestRunTableProps) {
  return (
    <ScrollReveal>
      <div className="rounded-xl border border-border/50 glass overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <h3 className="text-sm font-semibold text-foreground">
            Latest Benchmark Run
          </h3>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="w-3.5 h-3.5" />
            <span className="font-mono">{formatDateTime(run.completedAt)}</span>
            <span className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground text-[10px] font-mono uppercase">
              {run.schedule}
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px]">
            <thead>
              <tr className="border-b border-border/30">
                <th className="text-left text-[11px] font-medium text-muted-foreground py-2.5 px-4">
                  Model
                </th>
                <th className="text-center text-[11px] font-medium text-muted-foreground py-2.5 px-3">
                  Composite
                </th>
                <th className="text-center text-[11px] font-medium text-muted-foreground py-2.5 px-3">
                  Rank
                </th>
                <th className="text-center text-[11px] font-medium text-muted-foreground py-2.5 px-3">
                  Best Category
                </th>
                <th className="text-center text-[11px] font-medium text-muted-foreground py-2.5 px-3">
                  Worst Category
                </th>
                <th className="text-center text-[11px] font-medium text-muted-foreground py-2.5 px-3">
                  Details
                </th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => {
                const result = run.models[model.id];
                if (!result) return null;

                const catScores = Object.entries(result.categories).map(
                  ([catId, cat]) => ({ catId, score: cat.avgScore })
                );
                if (catScores.length === 0) return null;
                const best = catScores.reduce((a, b) =>
                  a.score > b.score ? a : b
                );
                const worst = catScores.reduce((a, b) =>
                  a.score < b.score ? a : b
                );
                const bestCat = CATEGORIES.find((c) => c.id === best.catId);
                const worstCat = CATEGORIES.find((c) => c.id === worst.catId);

                return (
                  <tr
                    key={model.id}
                    className="border-b border-border/20 hover:bg-muted/20 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: model.color }}
                        />
                        <span
                          className="font-medium text-sm"
                          style={{ color: model.color }}
                        >
                          {model.name}
                        </span>
                      </div>
                    </td>
                    <td className="text-center py-3 px-3">
                      <span
                        className={cn(
                          "font-mono font-bold text-sm",
                          getScoreColor(result.compositeScore)
                        )}
                      >
                        {formatScore(result.compositeScore)}
                      </span>
                    </td>
                    <td className="text-center py-3 px-3">
                      <span className="font-mono text-sm text-muted-foreground">
                        #{result.rank}
                      </span>
                    </td>
                    <td className="text-center py-3 px-3">
                      <div className="text-xs">
                        <span className="text-green-400 font-mono">
                          {formatScore(best.score)}
                        </span>
                        <span className="text-muted-foreground ml-1">
                          {bestCat?.name}
                        </span>
                      </div>
                    </td>
                    <td className="text-center py-3 px-3">
                      <div className="text-xs">
                        <span className="text-red-400 font-mono">
                          {formatScore(worst.score)}
                        </span>
                        <span className="text-muted-foreground ml-1">
                          {worstCat?.name}
                        </span>
                      </div>
                    </td>
                    <td className="text-center py-3 px-3">
                      <Link
                        href={`/models/${model.slug}`}
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
  );
}
