import { getLatestRun, getSynopsis, getRegressions, getTrends } from "@/lib/data";
import { MODELS } from "@/lib/models";
import { CATEGORIES } from "@/lib/categories";
import { SynopsisBanner } from "@/components/dashboard/synopsis-banner";
import { ModelOverviewCards } from "@/components/dashboard/model-overview-cards";
import { RegressionAlerts } from "@/components/dashboard/regression-alerts";
import { HeatmapGrid } from "@/components/charts/heatmap-grid";
import { PerformanceTimeline } from "@/components/dashboard/performance-timeline";
import { LatestRunTable } from "@/components/dashboard/latest-run-table";
import { ScrollReveal } from "@/components/shared/scroll-reveal";

export default function HomePage() {
  const latest = getLatestRun();
  const synopsis = getSynopsis();
  const regressions = getRegressions();
  const trends = getTrends("daily");

  const heatmapScores: Record<string, Record<string, number>> = {};
  for (const model of MODELS) {
    heatmapScores[model.id] = {};
    const modelResult = latest.models[model.id];
    if (modelResult) {
      for (const cat of CATEGORIES) {
        heatmapScores[model.id][cat.id] =
          modelResult.categories[cat.id]?.avgScore ?? 0;
      }
    }
  }

  const modelHistory: Record<string, number[]> = {};
  const modelChanges: Record<string, number> = {};
  for (const model of MODELS) {
    const allPoints = trends.data
      .slice(-21)
      .map((d) => d.models[model.id] ?? null);
    modelHistory[model.id] = allPoints.map((v) => v ?? 0);

    const valid = allPoints.filter((v): v is number => v !== null && v > 0);
    if (valid.length >= 2) {
      const recent = valid[valid.length - 1];
      const old = valid[0];
      modelChanges[model.id] = old > 0 ? ((recent - old) / old) * 100 : 0;
    } else {
      modelChanges[model.id] = 0;
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <SynopsisBanner synopsis={synopsis} />

      <ModelOverviewCards
        latest={latest}
        history={modelHistory}
        changes={modelChanges}
      />

      {/* Performance Timeline */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">
            Performance Timeline
          </h3>
          <PerformanceTimeline trends={trends} />
        </div>
      </ScrollReveal>

      {/* Regression Alerts */}
      <RegressionAlerts regressions={regressions.active} />

      {/* Category Heatmap */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">
            Category Performance Heatmap
          </h3>
          <HeatmapGrid scores={heatmapScores} />
        </div>
      </ScrollReveal>

      {/* Latest Run Table */}
      <LatestRunTable run={latest} />
    </div>
  );
}
