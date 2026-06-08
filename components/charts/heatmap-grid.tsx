"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { MODELS } from "@/lib/models";
import { CATEGORIES } from "@/lib/categories";
import { formatScore } from "@/lib/utils";

interface HeatmapGridProps {
  scores: Record<string, Record<string, number>>;
}

function getCellColor(score: number): string {
  if (score >= 90) return "bg-green-500/20 text-green-400 border-green-500/30";
  if (score >= 80) return "bg-lime-500/15 text-lime-400 border-lime-500/25";
  if (score >= 70)
    return "bg-yellow-500/15 text-yellow-400 border-yellow-500/25";
  if (score >= 60)
    return "bg-orange-500/15 text-orange-400 border-orange-500/25";
  return "bg-red-500/15 text-red-400 border-red-500/25";
}

export function HeatmapGrid({ scores }: HeatmapGridProps) {
  return (
    <>
      <div className="space-y-3 md:hidden">
        {CATEGORIES.map((category) => (
          <div
            key={category.id}
            className="rounded-lg border border-border/40 bg-muted/10 p-4"
          >
            <Link
              href={`/categories/${category.slug}`}
              className="text-sm font-semibold text-foreground hover:text-primary transition-colors"
            >
              {category.name}
            </Link>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {MODELS.map((model) => {
                const score = scores[model.id]?.[category.id] ?? 0;
                return (
                  <Link
                    key={model.id}
                    href={`/models/${model.slug}`}
                    className={cn(
                      "rounded-md border px-3 py-2 transition-all duration-200",
                      getCellColor(score)
                    )}
                  >
                    <p
                      className="text-[11px] font-medium"
                      style={{ color: model.color }}
                    >
                      {model.name}
                    </p>
                    <p className="mt-1 font-mono text-sm font-semibold">
                      {formatScore(score)}
                    </p>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[640px]">
          <thead>
            <tr>
              <th className="text-left text-xs font-medium text-muted-foreground py-2 px-3 w-44">
                Category
              </th>
              {MODELS.map((model) => (
                <th
                  key={model.id}
                  className="text-center text-xs font-medium py-2 px-2"
                  style={{ color: model.color }}
                >
                  {model.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CATEGORIES.map((category) => (
              <tr key={category.id} className="group">
                <td className="py-1.5 px-3">
                  <Link
                    href={`/categories/${category.slug}`}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {category.name}
                  </Link>
                </td>
                {MODELS.map((model) => {
                  const score = scores[model.id]?.[category.id] ?? 0;
                  return (
                    <td key={model.id} className="py-1.5 px-1.5">
                      <Link
                        href={`/models/${model.slug}`}
                        className={cn(
                          "block text-center py-2 px-2 rounded-md border font-mono text-sm font-medium transition-all duration-200 hover:scale-105",
                          getCellColor(score)
                        )}
                      >
                        {formatScore(score)}
                      </Link>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
