import { CATEGORIES } from "@/lib/categories";
import { getAllModels } from "@/lib/data";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import {
  Brain,
  Code,
  Bug,
  Puzzle,
  ShieldCheck,
  AlertTriangle,
  Lock,
  ListChecks,
  Star,
  Gauge,
  Monitor,
  Timer,
  Server,
  BarChart3,
  GitBranch,
} from "lucide-react";

const ICON_MAP: Record<string, React.ElementType> = {
  brain: Brain,
  code: Code,
  bug: Bug,
  puzzle: Puzzle,
  "shield-check": ShieldCheck,
  "alert-triangle": AlertTriangle,
  lock: Lock,
  "list-checks": ListChecks,
  star: Star,
  gauge: Gauge,
  monitor: Monitor,
};

export default function MethodologyPage() {
  const models = getAllModels();

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
      <ScrollReveal>
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-3">
            Methodology
          </h1>
          <p className="text-lg text-muted-foreground">
            How we benchmark frontier AI models — our test design, scoring
            system, and quality controls.
          </p>
        </div>
      </ScrollReveal>

      {/* Overview */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-6">
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            Overview
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div>
              <span className="text-3xl font-bold font-mono text-primary">
                33
              </span>
              <p className="text-sm text-muted-foreground mt-1">
                Individual tests per run
              </p>
            </div>
            <div>
              <span className="text-3xl font-bold font-mono text-primary">
                11
              </span>
              <p className="text-sm text-muted-foreground mt-1">
                Benchmark categories
              </p>
            </div>
            <div>
              <span className="text-3xl font-bold font-mono text-primary">
                1x
              </span>
              <p className="text-sm text-muted-foreground mt-1">
                Daily benchmark run (3am ET)
              </p>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Models */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-6">
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
            <Server className="w-5 h-5 text-primary" />
            Models Tested
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {models.map((model) => (
              <div
                key={model.id}
                className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 border border-border/30"
              >
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: model.color }}
                />
                <div>
                  <span className="font-medium text-sm" style={{ color: model.color }}>
                    {model.name}
                  </span>
                  <span className="text-xs text-muted-foreground ml-2">
                    {model.provider}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-4">
            Models are called through their configured adapters, including
            official CLIs and OpenRouter's chat-completions API. Temperature is
            set to 0.0 where the adapter supports it.
          </p>
        </div>
      </ScrollReveal>

      {/* Categories */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-6">
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-primary" />
            Benchmark Categories
          </h2>
          <div className="space-y-4">
            {CATEGORIES.map((cat) => {
              const Icon = ICON_MAP[cat.icon] || Brain;
              return (
                <div
                  key={cat.id}
                  className="flex gap-4 p-4 rounded-lg bg-muted/20 border border-border/30"
                >
                  <div className="flex-shrink-0 mt-0.5">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Icon className="w-4 h-4 text-primary" />
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-foreground">
                      {cat.name}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      {cat.description}
                    </p>
                    <span className="inline-block mt-2 text-[10px] font-mono text-muted-foreground/70">
                      Weight: {cat.weight}x &middot; 3 tests per run
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </ScrollReveal>

      {/* Scoring */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-6">
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            Scoring System
          </h2>
          <div className="space-y-4 text-sm text-muted-foreground">
            <p>
              Each test produces a score from 0 to 100. Scores are computed using
              one or more evaluation methods:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                {
                  name: "Code Execution",
                  desc: "Model-generated code runs in a Docker sandbox. Score based on test case pass rate.",
                },
                {
                  name: "LLM Judge",
                  desc: "A separate model evaluates the response against a rubric. Judge model differs from test subjects.",
                },
                {
                  name: "Pattern Matching",
                  desc: "Regex and structural checks verify format compliance, constraints, and output correctness.",
                },
                {
                  name: "Composite",
                  desc: "Combines multiple evaluators with weighted scoring for nuanced assessment.",
                },
              ].map((method) => (
                <div
                  key={method.name}
                  className="p-3 rounded-lg bg-muted/30 border border-border/30"
                >
                  <span className="font-medium text-foreground text-xs">
                    {method.name}
                  </span>
                  <p className="text-[11px] text-muted-foreground mt-1">
                    {method.desc}
                  </p>
                </div>
              ))}
            </div>
            <p>
              <strong className="text-foreground">Composite scores</strong> are
              weighted averages across all 11 categories. Weights reflect the
              relative importance of each capability. Current category weights
              are equal until enough run history exists to justify differentiated
              weighting.
            </p>
          </div>
        </div>
      </ScrollReveal>

      {/* Regression Detection */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-6">
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
            <Timer className="w-5 h-5 text-primary" />
            Regression Detection
          </h2>
          <div className="space-y-3 text-sm text-muted-foreground">
            <p>
              After each benchmark run, we compare scores against rolling
              historical averages:
            </p>
            <div className="space-y-2">
              {[
                { severity: "Minor", range: "3-5% drop", color: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20" },
                { severity: "Moderate", range: "5-15% drop", color: "text-orange-400 bg-orange-500/10 border-orange-500/20" },
                { severity: "Major", range: ">15% drop", color: "text-red-400 bg-red-500/10 border-red-500/20" },
              ].map(({ severity, range, color }) => (
                <div
                  key={severity}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium mr-2 ${color}`}
                >
                  {severity}: {range}
                </div>
              ))}
            </div>
            <p>
              A regression is considered &ldquo;resolved&rdquo; when the score
              returns to within 2% of the pre-regression average over 3
              consecutive runs.
            </p>
          </div>
        </div>
      </ScrollReveal>

      {/* Limitations */}
      <ScrollReveal>
        <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 p-6">
          <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            Limitations
          </h2>
          <ul className="space-y-2 text-sm text-muted-foreground list-disc list-inside">
            <li>
              LLM-as-judge evaluation introduces variability. We mitigate this
              with temperature 0.0 and structured rubrics.
            </li>
            <li>
              API performance can vary due to server load, rate limiting, and
              geographic location.
            </li>
            <li>
              33 tests cannot cover all capabilities. Results indicate trends,
              not absolute quality.
            </li>
            <li>
              Model versioning is opaque — providers may update models silently
              (which is exactly what we track).
            </li>
            <li>
              Code execution benchmarks are limited to Python and JavaScript in
              sandboxed environments.
            </li>
          </ul>
        </div>
      </ScrollReveal>
    </div>
  );
}
