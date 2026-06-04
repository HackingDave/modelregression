import { getLatestRun, getTrends } from "@/lib/data";
import { MODELS } from "@/lib/models";
import { CATEGORIES } from "@/lib/categories";
import { CompareClient } from "./compare-client";

export default function ComparePage() {
  const latest = getLatestRun();
  const trends = getTrends("daily");

  const allScores: Record<string, Record<string, number>> = {};
  for (const model of MODELS) {
    allScores[model.id] = {};
    const result = latest.models[model.id];
    if (result) {
      for (const cat of CATEGORIES) {
        allScores[model.id][cat.id] =
          result.categories[cat.id]?.avgScore ?? 0;
      }
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Compare Models
        </h1>
        <p className="text-muted-foreground">
          Side-by-side performance comparison across all benchmark categories.
        </p>
      </div>

      <CompareClient
        scores={allScores}
        trends={trends}
        latest={latest}
      />
    </div>
  );
}
