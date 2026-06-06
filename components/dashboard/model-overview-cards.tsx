"use client";

import { ModelOverviewCard } from "./model-overview-card";
import {
  StaggerContainer,
  StaggerItem,
} from "@/components/shared/scroll-reveal";
import type { LatestRun, ModelInfo } from "@/lib/types";

interface ModelOverviewCardsProps {
  latest: LatestRun;
  history: Record<string, number[]>;
  changes: Record<string, number>;
  models: ModelInfo[];
}

export function ModelOverviewCards({
  latest,
  history,
  changes,
  models,
}: ModelOverviewCardsProps) {
  return (
    <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {models.map((model) => {
        const result = latest.models[model.id];
        if (!result) return null;
        return (
          <StaggerItem key={model.id}>
            <ModelOverviewCard
              model={model}
              result={result}
              history={history[model.id] || []}
              change={changes[model.id] || 0}
            />
          </StaggerItem>
        );
      })}
    </StaggerContainer>
  );
}
