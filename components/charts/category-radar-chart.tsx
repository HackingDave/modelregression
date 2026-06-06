"use client";

import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { CATEGORIES } from "@/lib/categories";
import { MODELS } from "@/lib/models";
import type { ModelInfo } from "@/lib/types";

interface RadarDataPoint {
  category: string;
  fullMark: number;
  [modelId: string]: string | number;
}

interface CategoryRadarChartProps {
  scores: Record<string, Record<string, number>>;
  modelFilter?: string[];
  height?: number;
  models?: ModelInfo[];
}

export function CategoryRadarChart({
  scores,
  modelFilter,
  height = 400,
  models = MODELS,
}: CategoryRadarChartProps) {
  const data: RadarDataPoint[] = CATEGORIES.map((cat) => {
    const point: RadarDataPoint = {
      category: cat.name.replace("& ", "&\n"),
      fullMark: 100,
    };
    for (const modelId of Object.keys(scores)) {
      point[modelId] = scores[modelId]?.[cat.id] ?? 0;
    }
    return point;
  });

  const modelsToShow = modelFilter
    ? models.filter((m) => modelFilter.includes(m.id))
    : models.filter((m) => m.id in scores);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
        <PolarGrid stroke="hsl(222, 25%, 15%)" />
        <PolarAngleAxis
          dataKey="category"
          tick={{ fontSize: 10, fill: "hsl(220, 10%, 55%)" }}
        />
        <PolarRadiusAxis
          domain={[0, 100]}
          tick={{ fontSize: 9, fill: "hsl(220, 10%, 40%)" }}
          axisLine={false}
        />
        {modelsToShow.map((model) => (
          <Radar
            key={model.id}
            name={model.name}
            dataKey={model.id}
            stroke={model.color}
            fill={model.color}
            fillOpacity={0.1}
            strokeWidth={2}
          />
        ))}
        <Legend
          formatter={(value: string) => {
            const model = models.find((m) => m.name === value);
            return model?.name || value;
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
