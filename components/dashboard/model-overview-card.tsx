"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { formatScore, getScoreColor, getTrendIcon, getTrendColor } from "@/lib/utils";
import { Sparkline } from "@/components/charts/sparkline";
import { AnimatedCounter } from "@/components/shared/animated-counter";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { ModelInfo, ModelRunResult, HistoryEntry } from "@/lib/types";

interface ModelOverviewCardProps {
  model: ModelInfo;
  result: ModelRunResult;
  history: number[];
  change: number;
}

export function ModelOverviewCard({
  model,
  result,
  history,
  change,
}: ModelOverviewCardProps) {
  const trend = getTrendIcon(change);
  const TrendIcon =
    trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;

  return (
    <Link href={`/models/${model.slug}`} className="block group">
      <div className="relative rounded-xl border border-border/50 glass glass-hover card-shine transition-all duration-300 group-hover:border-opacity-80 p-5">
        {/* Top glow accent */}
        <div
          className="absolute top-0 left-4 right-4 h-px"
          style={{
            background: `linear-gradient(90deg, transparent, ${model.color}60, transparent)`,
          }}
        />

        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: model.color }}
            />
            <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
              {model.provider}
            </span>
          </div>
          <div
            className={cn(
              "flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono font-medium",
              change > 2
                ? "bg-green-500/10 text-green-400"
                : change < -2
                  ? "bg-red-500/10 text-red-400"
                  : "bg-yellow-500/10 text-yellow-400"
            )}
          >
            <TrendIcon className="w-3 h-3" />
            {change > 0 ? "+" : ""}
            {change.toFixed(1)}%
          </div>
        </div>

        {/* Model name */}
        <h3
          className="text-lg font-bold mb-1 transition-colors"
          style={{ color: model.color }}
        >
          {model.name}
        </h3>

        {/* Score + Rank */}
        <div className="flex items-end justify-between mb-4">
          <div>
            <AnimatedCounter
              value={result.compositeScore}
              className={cn("text-3xl font-bold", getScoreColor(result.compositeScore))}
            />
            <span className="text-sm text-muted-foreground font-mono ml-1">
              /100
            </span>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold font-mono text-muted-foreground">
              #{result.rank}
            </span>
          </div>
        </div>

        {/* Sparkline */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">7-day trend</span>
          <Sparkline data={history} color={model.color} width={100} height={28} />
        </div>
      </div>
    </Link>
  );
}
