"use client";

import { useState } from "react";
import { PerformanceLineChart } from "@/components/charts/performance-line-chart";
import { TimeRangeSelector } from "@/components/shared/time-range-selector";
import { MODELS } from "@/lib/models";
import type { TrendData, TimeRange } from "@/lib/types";

interface PerformanceTimelineProps {
  trends: TrendData;
}

export function PerformanceTimeline({ trends }: PerformanceTimelineProps) {
  const [range, setRange] = useState<TimeRange>("week");

  const sliceMap: Record<TimeRange, number> = {
    day: 3,
    week: 21,
    month: 90,
    year: 365,
  };

  const data = trends.data.slice(-(sliceMap[range] || 21));
  const sparseModels = MODELS.filter(
    (model) =>
      data.filter((point) => typeof point.models[model.id] === "number").length === 1
  );

  return (
    <div>
      <div className="flex justify-end mb-4">
        <TimeRangeSelector value={range} onChange={setRange} />
      </div>
      <PerformanceLineChart data={data} height={320} />
      {sparseModels.length > 0 && (
        <p className="mt-2 text-xs text-muted-foreground">
          New frontier versions with one completed run are shown as colored
          markers until their next run creates a trend line.
        </p>
      )}
    </div>
  );
}
