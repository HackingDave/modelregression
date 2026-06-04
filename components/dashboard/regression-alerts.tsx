"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { formatDate, formatPercent } from "@/lib/utils";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import type { Regression } from "@/lib/types";

interface RegressionAlertsProps {
  regressions: Regression[];
}

function getSeverityStyle(severity: string) {
  switch (severity) {
    case "major":
      return "border-red-500/40 bg-red-500/5";
    case "moderate":
      return "border-orange-500/40 bg-orange-500/5";
    default:
      return "border-yellow-500/40 bg-yellow-500/5";
  }
}

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

export function RegressionAlerts({ regressions }: RegressionAlertsProps) {
  if (regressions.length === 0) return null;

  return (
    <ScrollReveal>
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-orange-400" />
          <h3 className="text-sm font-semibold text-foreground">
            Active Regressions
          </h3>
          <span className="px-2 py-0.5 rounded-full text-xs font-mono bg-red-500/10 text-red-400 border border-red-500/20">
            {regressions.length}
          </span>
        </div>

        {regressions.map((reg, i) => (
          <Link
            key={reg.id}
            href={`/models/${reg.modelId}`}
            className={cn(
              "block rounded-lg border p-4 transition-all duration-200 hover:scale-[1.01]",
              getSeverityStyle(reg.severity)
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-foreground">
                    {reg.modelName}
                  </span>
                  <span
                    className={cn(
                      "px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-medium border",
                      getSeverityBadge(reg.severity)
                    )}
                  >
                    {reg.severity}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {reg.categoryName || "Overall"} dropped{" "}
                  <span className="font-mono text-red-400">
                    {formatPercent(reg.dropPct)}
                  </span>{" "}
                  from {reg.previousAvg.toFixed(1)} to{" "}
                  {reg.currentScore.toFixed(1)}
                </p>
                <p className="text-[10px] text-muted-foreground/70 mt-1">
                  Detected {formatDate(reg.detectedAt)} &middot; {reg.windowDays}
                  -day window
                </p>
              </div>
              <ArrowRight className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-1" />
            </div>
          </Link>
        ))}
      </div>
    </ScrollReveal>
  );
}
