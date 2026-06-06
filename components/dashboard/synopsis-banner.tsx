"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { AnimatedCounter } from "@/components/shared/animated-counter";
import { TimeRangeSelector } from "@/components/shared/time-range-selector";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import { Crown, TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { ModelInfo, Synopsis, TimeRange } from "@/lib/types";

interface SynopsisBannerProps {
  synopsis: Synopsis;
  models: ModelInfo[];
}

export function SynopsisBanner({ synopsis, models }: SynopsisBannerProps) {
  const [range, setRange] = useState<TimeRange>("day");

  const periodData = {
    day: synopsis.day,
    week: synopsis.week,
    month: synopsis.month,
    year: synopsis.month,
  };

  const current = periodData[range];
  const model = models.find((m) => m.id === current.modelId);
  const TrendIcon =
    current.change > 2
      ? TrendingUp
      : current.change < -2
        ? TrendingDown
        : Minus;

  return (
    <ScrollReveal>
      <div className="relative overflow-hidden rounded-2xl border border-border/50 glass">
        {/* Gradient background */}
        <div
          className="absolute inset-0 opacity-10"
          style={{
            background: `radial-gradient(ellipse at 30% 50%, ${model?.color || "#22C55E"}40, transparent 70%)`,
          }}
        />

        <div className="relative p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                <Crown className="w-5 h-5 text-yellow-500" />
              </div>
              <div>
                <h2 className="text-sm font-medium text-muted-foreground">
                  Top Performing Model
                </h2>
                <p className="text-xs text-muted-foreground/70 mt-0.5">
                  Based on composite benchmark scores
                </p>
              </div>
            </div>
            <TimeRangeSelector value={range} onChange={setRange} />
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-end gap-6">
            {/* Model info */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: model?.color }}
                />
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                  {model?.provider}
                </span>
              </div>
              <h1
                className="text-3xl sm:text-4xl font-bold mb-1"
                style={{ color: model?.color }}
              >
                {current.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                {range === "day"
                  ? "Leading today's benchmarks"
                  : range === "week"
                    ? "Best average this week"
                    : "Best average this month"}
              </p>
            </div>

            {/* Score */}
            <div className="text-right">
              <div className="flex items-baseline gap-2">
                <AnimatedCounter
                  value={current.score}
                  className="text-5xl sm:text-6xl font-bold text-foreground"
                />
                <span className="text-lg text-muted-foreground font-mono">
                  /100
                </span>
              </div>
              <div className="flex items-center justify-end gap-1.5 mt-2">
                <TrendIcon
                  className={cn(
                    "w-4 h-4",
                    current.change > 2
                      ? "text-green-400"
                      : current.change < -2
                        ? "text-red-400"
                        : "text-yellow-400"
                  )}
                />
                <span
                  className={cn(
                    "text-sm font-mono font-medium",
                    current.change > 2
                      ? "text-green-400"
                      : current.change < -2
                        ? "text-red-400"
                        : "text-yellow-400"
                  )}
                >
                  {current.change > 0 ? "+" : ""}
                  {current.change.toFixed(1)}%
                </span>
                <span className="text-xs text-muted-foreground">
                  vs prev {range}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ScrollReveal>
  );
}
