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

interface RadarDataPoint {
  category: string;
  fullMark: number;
  [modelId: string]: string | number;
}

interface CategoryRadarChartProps {
  scores: Record<string, Record<string, number>>;
  modelFilter?: string[];
  height?: number;
}

export function CategoryRadarChart({
  scores,
  modelFilter,
  height = 400,
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
    ? MODELS.filter((m) => modelFilter.includes(m.id))
    : MODELS.filter((m) => m.id in scores);

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
            const model = MODELS.find((m) => m.name === value);
            return model?.name || value;
          }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
