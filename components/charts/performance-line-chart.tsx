"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { MODELS } from "@/lib/models";
import { formatDateTime } from "@/lib/utils";

interface DataPoint {
  timestamp: string;
  models: Record<string, number>;
}

type ChartPoint = {
  timestamp: string;
  label: string;
} & Record<string, string | number>;

interface PerformanceLineChartProps {
  data: DataPoint[];
  height?: number;
  showLegend?: boolean;
  modelFilter?: string[];
}

export function PerformanceLineChart({
  data,
  height = 350,
  showLegend = true,
  modelFilter,
}: PerformanceLineChartProps) {
  const modelsToShow = modelFilter
    ? MODELS.filter((m) => modelFilter.includes(m.id))
    : MODELS;

  const chartData: ChartPoint[] = data.map((d) => ({
    timestamp: d.timestamp,
    label: formatDateTime(d.timestamp),
    ...d.models,
  }));

  const visibleValues = chartData.flatMap((point) =>
    modelsToShow
      .map((model) => point[model.id])
      .filter((value): value is number => typeof value === "number")
  );
  const minVisibleValue =
    visibleValues.length > 0 ? Math.min(...visibleValues) : 50;
  const yAxisMin =
    minVisibleValue < 50
      ? Math.max(0, Math.floor(minVisibleValue / 10) * 10)
      : 50;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 25%, 12%)" />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11 }}
          interval="preserveStartEnd"
          tickLine={false}
        />
        <YAxis
          domain={[yAxisMin, 100]}
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            background: "hsl(222, 25%, 10%)",
            border: "1px solid hsl(222, 25%, 18%)",
            borderRadius: "8px",
            boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
          }}
          labelStyle={{
            color: "hsl(210, 20%, 85%)",
            fontWeight: 600,
            fontFamily: "JetBrains Mono, monospace",
            fontSize: 12,
          }}
          formatter={(value: number, name: string) => {
            const model = MODELS.find((m) => m.id === name);
            return [value.toFixed(1), model?.name || name];
          }}
        />
        {showLegend && (
          <Legend
            formatter={(value: string) => {
              const model = MODELS.find((m) => m.id === value);
              return model?.name || value;
            }}
          />
        )}
        {modelsToShow.map((model) => (
          <Line
            key={model.id}
            type="monotone"
            dataKey={model.id}
            stroke={model.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 2 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
