"use client";

import { MODELS } from "@/lib/models";
import { ModelOverviewCard } from "./model-overview-card";
import {
  StaggerContainer,
  StaggerItem,
} from "@/components/shared/scroll-reveal";
import type { LatestRun } from "@/lib/types";

interface ModelOverviewCardsProps {
  latest: LatestRun;
  history: Record<string, number[]>;
  changes: Record<string, number>;
}

export function ModelOverviewCards({
  latest,
  history,
  changes,
}: ModelOverviewCardsProps) {
  return (
    <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      {MODELS.map((model) => {
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
