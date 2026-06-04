"use client";

import { useState } from "react";
import { PerformanceLineChart } from "@/components/charts/performance-line-chart";
import { TimeRangeSelector } from "@/components/shared/time-range-selector";
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

  return (
    <div>
      <div className="flex justify-end mb-4">
        <TimeRangeSelector value={range} onChange={setRange} />
      </div>
      <PerformanceLineChart data={data} height={320} />
    </div>
  );
}
