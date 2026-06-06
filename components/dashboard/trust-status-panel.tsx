import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  Eye,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { cn, formatDateTime } from "@/lib/utils";
import type { LatestRun, ModelInfo, Regression } from "@/lib/types";

interface TrustStatusPanelProps {
  latest: LatestRun;
  models: ModelInfo[];
  activeRegressions: Regression[];
  changes: Record<string, number>;
}

type TrustStatus = "good" | "watch" | "do-not-trust-alone";

interface TrustReadout {
  model: ModelInfo;
  status: TrustStatus;
  label: string;
  badgeClass: string;
  icon: typeof ShieldCheck;
  securityScore: number;
  thoroughnessScore: number;
  compositeScore: number;
  change: number;
  activeRegression?: Regression;
  weakestSecurityTest?: { testId: string; name: string; score: number };
  problem: string;
  useItFor: string;
  dontUseItFor: string;
}

function statusRank(status: TrustStatus) {
  switch (status) {
    case "good":
      return 0;
    case "watch":
      return 1;
    default:
      return 2;
  }
}

function buildReadout(
  model: ModelInfo,
  latest: LatestRun,
  activeRegressions: Regression[],
  change: number
): TrustReadout | null {
  const result = latest.models[model.id];
  if (!result) return null;

  const security = result.categories["security-awareness"];
  const thoroughness = result.categories["code-thoroughness"];
  const securityScore = security?.avgScore ?? 0;
  const thoroughnessScore = thoroughness?.avgScore ?? 0;
  const activeRegression = activeRegressions.find(
    (reg) => reg.modelId === model.id
  );
  const weakestSecurityTest = security?.tests
    ? [...security.tests].sort((a, b) => a.score - b.score)[0]
    : undefined;

  let status: TrustStatus = "good";
  if (
    activeRegression?.severity === "major" ||
    securityScore < 85 ||
    result.compositeScore < 88
  ) {
    status = "do-not-trust-alone";
  } else if (
    activeRegression ||
    securityScore < 93 ||
    thoroughnessScore < 80 ||
    result.compositeScore < 91 ||
    change < -2
  ) {
    status = "watch";
  }

  const statusCopy = {
    good: {
      label: "Good",
      badgeClass: "border-emerald-400/35 bg-emerald-400/10 text-emerald-300",
      icon: ShieldCheck,
    },
    watch: {
      label: "Watch",
      badgeClass: "border-amber-400/35 bg-amber-400/10 text-amber-300",
      icon: Eye,
    },
    "do-not-trust-alone": {
      label: "Do not trust alone",
      badgeClass: "border-red-400/40 bg-red-400/10 text-red-300",
      icon: ShieldAlert,
    },
  }[status];

  const weakPoint = weakestSecurityTest
    ? `${weakestSecurityTest.name} scored ${weakestSecurityTest.score.toFixed(1)}`
    : "Security evidence is thin today";

  let problem = "No active regression in the current run.";
  if (activeRegression) {
    problem = `${activeRegression.categoryName || "Overall"} dropped ${Math.abs(
      activeRegression.dropPct
    ).toFixed(1)}% over ${activeRegression.windowDays} days.`;
  } else if (securityScore < 93) {
    problem = `${weakPoint}. Do not round that up to fine.`;
  } else if (thoroughnessScore < 80) {
    problem = `Security looks strong, but thoroughness is only ${thoroughnessScore.toFixed(
      1
    )}.`;
  }

  let useItFor = "Security review support and second-pass cleanup.";
  let dontUseItFor = "Final approval without human review.";
  if (status === "watch") {
    useItFor = "Drafting, triage, and finding obvious misses.";
    dontUseItFor = "The final answer on risky changes.";
  }
  if (status === "do-not-trust-alone") {
    useItFor = "Brainstorming and quick comparison only.";
    dontUseItFor = "Incident response, security fixes, or compliance calls.";
  }

  return {
    model,
    status,
    label: statusCopy.label,
    badgeClass: statusCopy.badgeClass,
    icon: statusCopy.icon,
    securityScore,
    thoroughnessScore,
    compositeScore: result.compositeScore,
    change,
    activeRegression,
    weakestSecurityTest,
    problem,
    useItFor,
    dontUseItFor,
  };
}

export function TrustStatusPanel({
  latest,
  models,
  activeRegressions,
  changes,
}: TrustStatusPanelProps) {
  const readouts = models
    .map((model) =>
      buildReadout(model, latest, activeRegressions, changes[model.id] ?? 0)
    )
    .filter((readout): readout is TrustReadout => Boolean(readout))
    .sort((a, b) => {
      const statusDelta = statusRank(a.status) - statusRank(b.status);
      if (statusDelta !== 0) return statusDelta;
      return b.securityScore - a.securityScore;
    });

  const best = readouts[0];
  const riskiest = [...readouts].sort((a, b) => {
    const statusDelta = statusRank(b.status) - statusRank(a.status);
    if (statusDelta !== 0) return statusDelta;
    return a.securityScore - b.securityScore;
  })[0];

  return (
    <section className="relative overflow-hidden rounded-xl border border-border/50 glass">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-red-400/70 to-transparent" />
      <div className="p-5 sm:p-6">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 border-b border-border/60 pb-5">
          <div className="max-w-2xl">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-red-300" />
              <span className="text-xs font-mono uppercase tracking-[0.22em] text-red-200/80">
                No vendor spin
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
              Can I trust this model today?
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Short answer from today&apos;s receipts. Good means useful. It
              does not mean let it ship security work by itself.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 lg:min-w-[420px]">
            <div className="border border-emerald-400/20 bg-emerald-400/5 rounded-lg p-3">
              <p className="text-[10px] font-mono uppercase tracking-wider text-emerald-200/70">
                Best current answer
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {best?.model.name ?? "No model data"}
              </p>
              <p className="text-xs text-muted-foreground">
                {best
                  ? `${best.securityScore.toFixed(1)} security score`
                  : "Waiting on benchmark export"}
              </p>
            </div>
            <div className="border border-red-400/20 bg-red-400/5 rounded-lg p-3">
              <p className="text-[10px] font-mono uppercase tracking-wider text-red-200/70">
                Watch first
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">
                {riskiest?.model.name ?? "No model data"}
              </p>
              <p className="text-xs text-muted-foreground">
                {riskiest ? riskiest.problem : "No active readout"}
              </p>
            </div>
          </div>
        </div>

        <div className="divide-y divide-border/55">
          {readouts.map((readout) => {
            const StatusIcon = readout.icon;
            const evidenceHref = readout.weakestSecurityTest
              ? `/evidence/${latest.runId}/${readout.weakestSecurityTest.testId}`
              : `/models/${readout.model.slug}`;

            return (
              <div
                key={readout.model.id}
                className="grid grid-cols-1 xl:grid-cols-[220px_1fr_260px] gap-4 py-5"
              >
                <div className="flex items-start gap-3">
                  <div
                    className="mt-1 h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: readout.model.color }}
                  />
                  <div>
                    <Link
                      href={`/models/${readout.model.slug}`}
                      className="font-semibold text-foreground hover:text-primary transition-colors"
                    >
                      {readout.model.name}
                    </Link>
                    <div className="mt-2">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[11px] font-mono uppercase tracking-wide",
                          readout.badgeClass
                        )}
                      >
                        <StatusIcon className="h-3 w-3" />
                        {readout.label}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <p className="text-sm text-foreground">{readout.problem}</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                        Use it for
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {readout.useItFor}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                        Don&apos;t use it for
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {readout.dontUseItFor}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 xl:grid-cols-1 gap-2 text-xs">
                  <div className="rounded-lg border border-border/50 bg-black/15 px-3 py-2">
                    <p className="font-mono text-muted-foreground">Security</p>
                    <p className="text-sm font-semibold text-foreground">
                      {readout.securityScore.toFixed(1)}
                    </p>
                  </div>
                  <div className="rounded-lg border border-border/50 bg-black/15 px-3 py-2">
                    <p className="font-mono text-muted-foreground">Overall</p>
                    <p className="text-sm font-semibold text-foreground">
                      {readout.compositeScore.toFixed(1)}
                    </p>
                  </div>
                  <Link
                    href={evidenceHref}
                    className="group rounded-lg border border-border/50 bg-black/15 px-3 py-2 hover:border-primary/40 transition-colors"
                  >
                    <p className="font-mono text-muted-foreground">Receipts</p>
                    <p className="flex items-center gap-1 text-sm font-semibold text-foreground">
                      Open
                      <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
                    </p>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>

        <p className="border-t border-border/60 pt-4 text-[11px] text-muted-foreground">
          Latest run completed {formatDateTime(latest.completedAt)}. Labels are
          derived from benchmark scores, active regression flags, and the
          weakest security-awareness receipt in the current run.
        </p>
      </div>
    </section>
  );
}
