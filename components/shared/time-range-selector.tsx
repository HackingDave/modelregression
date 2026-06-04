"use client";

import { cn } from "@/lib/utils";
import type { TimeRange } from "@/lib/types";

interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
  className?: string;
}

const RANGES: { value: TimeRange; label: string }[] = [
  { value: "day", label: "24h" },
  { value: "week", label: "7d" },
  { value: "month", label: "30d" },
  { value: "year", label: "1y" },
];

export function TimeRangeSelector({
  value,
  onChange,
  className,
}: TimeRangeSelectorProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 p-1 rounded-lg bg-muted/50 border border-border/50",
        className
      )}
    >
      {RANGES.map(({ value: v, label }) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          className={cn(
            "px-3 py-1.5 rounded-md text-xs font-mono font-medium transition-all duration-200",
            v === value
              ? "bg-primary/15 text-primary shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
