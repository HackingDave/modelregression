"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { formatScore, getScoreColor, formatDateTime, formatTokens } from "@/lib/utils";
import { MODELS } from "@/lib/models";
import { CATEGORIES, TOKEN_EFFICIENCY_CATEGORY_ID } from "@/lib/categories";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import { Clock, ExternalLink, Hash } from "lucide-react";
import type { LatestRun } from "@/lib/types";

interface LatestRunTableProps {
  run: LatestRun;
}

interface LatestRunTableRow {
  model: (typeof MODELS)[number];
  result: LatestRun["models"][string];
  best: { catId: string; score: number };
  worst: { catId: string; score: number };
  bestCat: (typeof CATEGORIES)[number] | undefined;
  worstCat: (typeof CATEGORIES)[number] | undefined;
  tokenBenchmark: number | null;
}

export function LatestRunTable({ run }: LatestRunTableProps) {
  const rows = MODELS.map((model) => {
    const result = run.models[model.id];
    if (!result) return null;

    const catScores = Object.entries(result.categories).map(([catId, cat]) => ({
      catId,
      score: cat.avgScore ?? 0,
    }));
    if (catScores.length === 0) return null;

    const best = catScores.reduce((a, b) => (a.score > b.score ? a : b));
    const worst = catScores.reduce((a, b) => (a.score < b.score ? a : b));
    const bestCat = CATEGORIES.find((c) => c.id === best.catId);
    const worstCat = CATEGORIES.find((c) => c.id === worst.catId);
    const tokenBenchmark =
      result.categories[TOKEN_EFFICIENCY_CATEGORY_ID]?.avgScore ?? null;

    return {
      model,
      result,
      best,
      worst,
      bestCat,
      worstCat,
      tokenBenchmark,
    };
  }).filter((row): row is LatestRunTableRow => row !== null);

  return (
    <ScrollReveal>
      <div className="rounded-xl border border-border/50 glass overflow-hidden">
        <div className="flex flex-col gap-3 p-4 border-b border-border/50 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-sm font-semibold text-foreground">
            Latest Benchmark Run
          </h3>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <Clock className="w-3.5 h-3.5" />
            <span className="font-mono">{formatDateTime(run.completedAt)}</span>
            <span className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground text-[10px] font-mono uppercase">
              {run.schedule}
            </span>
          </div>
        </div>

        <div className="grid gap-3 p-4 md:hidden">
          {rows.map(({ model, result, best, worst, bestCat, worstCat, tokenBenchmark }) => (
            <div
              key={model.id}
              className="rounded-lg border border-border/40 bg-muted/10 p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2.5">
                    <div
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: model.color }}
                    />
                    <span
                      className="font-semibold text-sm"
                      style={{ color: model.color }}
                    >
                      {model.name}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Composite benchmark summary
                  </p>
                </div>
                <span className="rounded-full bg-muted px-2 py-1 text-[11px] font-mono text-muted-foreground">
                  {result.rank != null ? `#${result.rank}` : "—"}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-border/30 bg-background/30 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                    Composite
                  </p>
                  <p className={cn("mt-1 font-mono text-lg font-bold", getScoreColor(result.compositeScore))}>
                    {formatScore(result.compositeScore)}
                  </p>
                </div>
                <div className="rounded-lg border border-border/30 bg-background/30 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                    Token Benchmark
                  </p>
                  <p className={cn("mt-1 font-mono text-lg font-bold", getScoreColor(tokenBenchmark))}>
                    {formatScore(tokenBenchmark)}
                  </p>
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between rounded-lg border border-border/30 bg-background/30 px-3 py-2">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Hash className="h-3.5 w-3.5" />
                  <span>Total tokens</span>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm text-foreground">
                    {formatTokens(result.totalTokens)}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    ~{formatTokens(result.avgTokensPerTest)}/test
                  </p>
                </div>
              </div>

              <div className="mt-3 space-y-2 text-xs">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-muted-foreground">Best category</span>
                  <span className="text-right">
                    <span className="font-mono text-green-400">{formatScore(best.score)}</span>{" "}
                    <span className="text-muted-foreground">{bestCat?.name}</span>
                  </span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-muted-foreground">Worst category</span>
                  <span className="text-right">
                    <span className="font-mono text-red-400">{formatScore(worst.score)}</span>{" "}
                    <span className="text-muted-foreground">{worstCat?.name}</span>
                  </span>
                </div>
              </div>

              <Link
                href={`/models/${model.slug}`}
                className="mt-4 inline-flex items-center gap-1 text-xs text-primary hover:underline"
              >
                View details
                <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          ))}
        </div>

        <div className="hidden overflow-x-auto md:block">
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
                  Tokens
                </th>
                <th className="text-center text-[11px] font-medium text-muted-foreground py-2.5 px-3">
                  Details
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ model, result, best, worst, bestCat, worstCat }) => (
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
                      {result.rank != null ? `#${result.rank}` : "—"}
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
                    <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
                      <Hash className="w-3 h-3" />
                      <span className="font-mono">
                        {formatTokens(result.totalTokens)}
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
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </ScrollReveal>
  );
}
