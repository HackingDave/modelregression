import { CircleDollarSign, ExternalLink } from "lucide-react";
import { formatDateTime } from "@/lib/utils";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import type { OpenRouterPricingData } from "@/lib/types";

interface OpenRouterCostPanelProps {
  pricing: OpenRouterPricingData;
}

function moneyPerM(value: number | null | undefined): string {
  if (value == null) return "n/a";
  if (value === 0) return "$0";
  if (value > 0 && value < 0.01) return "<$0.01";
  return `$${value.toLocaleString("en-US", {
    minimumFractionDigits: value < 10 ? 2 : 0,
    maximumFractionDigits: value < 10 ? 4 : 2,
  })}`;
}

function compactNumber(value: number | null | undefined): string {
  if (value == null) return "n/a";
  return value.toLocaleString("en-US");
}

export function OpenRouterCostPanel({ pricing }: OpenRouterCostPanelProps) {
  const paid = pricing.models.filter((entry) => !entry.isFree);
  const cheapest = paid[0];
  const rows = paid.slice(0, 6);

  return (
    <ScrollReveal>
      <section className="rounded-xl border border-border/50 glass overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 p-5 border-b border-border/50">
          <div className="flex items-start gap-3">
            <div className="rounded-lg border border-cyan-400/25 bg-cyan-400/10 p-2">
              <CircleDollarSign className="h-4 w-4 text-cyan-300" />
            </div>
            <div>
              <p className="text-[10px] font-mono uppercase tracking-[0.24em] text-cyan-200/75">
                OpenRouter cost watch
              </p>
              <h2 className="mt-1 text-lg font-semibold text-foreground">
                Cost per 1M tokens, refreshed daily
              </h2>
              <p className="mt-1 max-w-2xl text-xs text-muted-foreground">
                Pulled from OpenRouter&apos;s model catalog during JSON export.
                Cheap does not mean good. It just means cheap.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs lg:min-w-[440px]">
            <div className="rounded-lg border border-border/50 bg-black/15 px-3 py-2">
              <p className="font-mono text-muted-foreground">Catalog</p>
              <p className="text-sm font-semibold text-foreground">
                {pricing.modelCount.toLocaleString()}
              </p>
            </div>
            <div className="rounded-lg border border-border/50 bg-black/15 px-3 py-2">
              <p className="font-mono text-muted-foreground">Free</p>
              <p className="text-sm font-semibold text-foreground">
                {pricing.freeModelCount.toLocaleString()}
              </p>
            </div>
            <div className="rounded-lg border border-border/50 bg-black/15 px-3 py-2">
              <p className="font-mono text-muted-foreground">Cheapest</p>
              <p className="text-sm font-semibold text-foreground">
                {cheapest
                  ? moneyPerM(cheapest.blendedOneInOneOutPerM)
                  : "n/a"}
              </p>
            </div>
          </div>
        </div>

        <div className="p-5">
          <div className="mb-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <h3 className="text-sm font-semibold text-foreground">
              Cheapest paid catalog entries
            </h3>
            <a
              href={pricing.source}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              OpenRouter source
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          {pricing.error && (
            <div className="mb-3 rounded-lg border border-red-400/25 bg-red-400/10 px-3 py-2 text-xs text-red-200">
              Latest refresh failed: {pricing.error}
            </div>
          )}

          {rows.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px]">
                <thead>
                  <tr className="border-b border-border/30">
                    <th className="text-left py-2.5 pr-4 text-[11px] font-medium text-muted-foreground">
                      Model
                    </th>
                    <th className="text-right py-2.5 px-3 text-[11px] font-medium text-muted-foreground">
                      Input / 1M
                    </th>
                    <th className="text-right py-2.5 px-3 text-[11px] font-medium text-muted-foreground">
                      Output / 1M
                    </th>
                    <th className="text-right py-2.5 px-3 text-[11px] font-medium text-muted-foreground">
                      1M in + 1M out
                    </th>
                    <th className="text-right py-2.5 pl-3 text-[11px] font-medium text-muted-foreground">
                      Context
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((entry) => (
                    <tr
                      key={entry.id}
                      className="border-b border-border/20 hover:bg-muted/10 transition-colors"
                    >
                      <td className="py-3 pr-4">
                        <p className="text-sm font-medium text-foreground">
                          {entry.name}
                        </p>
                        <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
                          {entry.id}
                        </p>
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-sm text-foreground">
                        {moneyPerM(entry.promptPerMTok)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-sm text-foreground">
                        {moneyPerM(entry.completionPerMTok)}
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-sm font-semibold text-cyan-200">
                        {moneyPerM(entry.blendedOneInOneOutPerM)}
                      </td>
                      <td className="py-3 pl-3 text-right font-mono text-xs text-muted-foreground">
                        {compactNumber(entry.contextLength)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-lg border border-border/50 bg-black/15 px-4 py-5 text-sm text-muted-foreground">
              No OpenRouter prices are available in the latest exported catalog.
            </div>
          )}

          <p className="mt-4 text-[11px] text-muted-foreground">
            Last refreshed {formatDateTime(pricing.updatedAt)}. Prices are
            normalized from OpenRouter per-token catalog values into dollars per
            million tokens.
          </p>
        </div>
      </section>
    </ScrollReveal>
  );
}
