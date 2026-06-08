import { getEvidence, getAllEvidencePaths } from "@/lib/data";
import { getModel } from "@/lib/models";
import { getCategory } from "@/lib/categories";
import { formatScore, getScoreColor, cn } from "@/lib/utils";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import Link from "next/link";
import {
  ArrowLeft,
  FileText,
  Clock,
  Hash,
  AlertCircle,
} from "lucide-react";

export async function generateStaticParams() {
  return getAllEvidencePaths();
}

export default async function EvidencePage({
  params,
}: {
  params: Promise<{ runId: string; testId: string }>;
}) {
  const { runId, testId } = await params;
  let evidence;
  try {
    evidence = getEvidence(runId, testId);
  } catch {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
        <h1 className="text-xl font-bold text-foreground mb-2">
          Evidence Not Found
        </h1>
        <p className="text-muted-foreground mb-4">
          This evidence file may have been pruned or the run ID is invalid.
        </p>
        <Link href="/" className="text-primary hover:underline text-sm">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const category = getCategory(evidence.test.category);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back link */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      {/* Test info */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono text-muted-foreground">
              {runId}
            </span>
            <span className="text-muted-foreground">/</span>
            <Link
              href={`/categories/${category?.slug || evidence.test.category}`}
              className="text-xs text-primary hover:underline"
            >
              {evidence.test.categoryName}
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            {evidence.test.name}
          </h1>
          <p className="text-muted-foreground text-sm mb-4">
            {evidence.test.description}
          </p>

          {/* Prompt */}
          <div className="mt-4">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-2">
              <FileText className="w-3.5 h-3.5" />
              Prompt Sent to Models
            </h3>
            <div className="rounded-lg bg-muted/30 border border-border/30 p-4">
              <pre className="text-sm text-foreground whitespace-pre-wrap font-mono leading-relaxed">
                {evidence.test.prompt}
              </pre>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Model Results */}
      <div className="space-y-6">
        {Object.entries(evidence.results)
          .sort((a, b) => (b[1].score ?? -1) - (a[1].score ?? -1))
          .map(([modelId, result]) => {
            const model = getModel(modelId);
            if (!model) return null;

            return (
              <ScrollReveal key={modelId}>
                <div className="rounded-xl border border-border/50 glass overflow-hidden">
                  {/* Header */}
                  <div
                    className="px-5 py-3 border-b border-border/50 flex items-center justify-between"
                    style={{
                      background: `linear-gradient(90deg, ${model.color}08, transparent)`,
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: model.color }}
                      />
                      <span
                        className="font-bold text-sm"
                        style={{ color: model.color }}
                      >
                        {model.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      {result.latencyMs != null && (
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Clock className="w-3.5 h-3.5" />
                          <span className="font-mono">
                            {(result.latencyMs / 1000).toFixed(1)}s
                          </span>
                        </div>
                      )}
                      {result.tokenCount != null && result.tokenCount > 0 && (
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Hash className="w-3.5 h-3.5" />
                          <span className="font-mono">
                            {result.tokenCount.toLocaleString()} tokens
                            {result.promptTokens != null && result.completionTokens != null && (
                              <span className="text-muted-foreground/60 ml-1">
                                ({result.promptTokens.toLocaleString()} in / {result.completionTokens.toLocaleString()} out)
                              </span>
                            )}
                          </span>
                        </div>
                      )}
                      <span
                        className={cn(
                          "font-mono font-bold text-lg",
                          getScoreColor(result.score)
                        )}
                      >
                        {formatScore(result.score)}
                      </span>
                    </div>
                  </div>

                  {/* Output */}
                  <div className="p-5">
                    {result.error ? (
                      <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-4">
                        <p className="text-sm text-red-400 font-mono">
                          Error: {result.error}
                        </p>
                      </div>
                    ) : (
                      <div className="rounded-lg bg-muted/20 border border-border/30 p-4 max-h-96 overflow-y-auto">
                        <pre className="text-xs text-foreground/90 whitespace-pre-wrap font-mono leading-relaxed">
                          {result.modelOutput}
                        </pre>
                      </div>
                    )}

                    {/* Eval details */}
                    {result.evalDetails &&
                      Object.keys(result.evalDetails).length > 0 && (
                        <div className="mt-4">
                          <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                            Evaluation Details
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(result.evalDetails).map(
                              ([key, value]) => (
                                <span
                                  key={key}
                                  className="px-2 py-1 rounded bg-muted/40 border border-border/30 text-[11px] font-mono text-muted-foreground"
                                >
                                  {key}:{" "}
                                  <span className="text-foreground">
                                    {typeof value === "object"
                                      ? JSON.stringify(value)
                                      : String(value)}
                                  </span>
                                </span>
                              )
                            )}
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              </ScrollReveal>
            );
          })}
      </div>
    </div>
  );
}
