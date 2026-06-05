import Image from "next/image";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import {
  Shield,
  Activity,
  Github,
  Twitter,
  Globe,
  ExternalLink,
} from "lucide-react";

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
      {/* Hero */}
      <ScrollReveal>
        <div className="relative rounded-2xl border border-border/50 glass overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-blue-500/5" />
          <div className="relative p-8 sm:p-12">
            <div className="flex flex-col sm:flex-row items-start gap-8">
              {/* Photo */}
              <div className="flex-shrink-0">
                <div className="relative">
                  <Image
                    src="/images/david-kennedy.jpg"
                    alt="David Kennedy"
                    width={180}
                    height={180}
                    className="rounded-xl object-cover"
                  />
                  <div className="absolute inset-0 rounded-xl ring-1 ring-white/10" />
                </div>
              </div>

              {/* Bio */}
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-1">
                  David Kennedy
                </h1>
                <p className="text-lg text-primary mb-4">
                  Founder of TrustedSec &amp; Binary Defense
                </p>
                <p className="text-muted-foreground leading-relaxed">
                  David Kennedy is the founder of{" "}
                  <a
                    href="https://www.trustedsec.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    TrustedSec
                  </a>
                  , an information security consulting company, and{" "}
                  <a
                    href="https://www.binarydefense.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Binary Defense
                  </a>
                  , a managed security services provider. He is a former hacker
                  for the NSA and a Marine, and has been a leader in the
                  cybersecurity industry for over two decades. David is the
                  creator of several widely-used open-source security tools and
                  is a frequent speaker at major security conferences worldwide.
                </p>

                {/* Links */}
                <div className="flex items-center gap-3 mt-5">
                  <a
                    href="https://twitter.com/HackingDave"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border/50 text-sm text-muted-foreground hover:text-foreground hover:border-border transition-colors"
                  >
                    <Twitter className="w-4 h-4" />
                    @HackingDave
                  </a>
                  <a
                    href="https://github.com/HackingDave"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border/50 text-sm text-muted-foreground hover:text-foreground hover:border-border transition-colors"
                  >
                    <Github className="w-4 h-4" />
                    GitHub
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Why This Project */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-xl bg-primary/10">
              <Activity className="w-5 h-5 text-primary" />
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              Why ModelRegression.com?
            </h2>
          </div>

          <div className="space-y-4 text-muted-foreground leading-relaxed">
            <p>
              As someone who has spent their career breaking into systems and
              defending against attacks, I&apos;ve learned one thing: you can&apos;t
              defend what you can&apos;t measure. The same principle applies to AI
              models.
            </p>
            <p>
              I started noticing that frontier AI models — the ones we rely on
              for coding, analysis, and security work — would{" "}
              <strong className="text-foreground">
                silently degrade without any announcement
              </strong>
              . One day a model is exceptional at finding bugs in code, and the
              next week it&apos;s introducing them. Providers don&apos;t always
              communicate these changes, and by the time you notice, you&apos;ve
              already shipped code reviewed by a model that was performing below
              its previous standard.
            </p>
            <p>
              This project exists because the AI community deserves
              transparency. ModelRegression.com runs{" "}
              <strong className="text-foreground">
                automated benchmarks every day
              </strong>{" "}
              against every major frontier model, tracking performance across
              real-world tasks: coding, bug detection, security analysis,
              reasoning, and more.
            </p>
            <p>
              When a model regresses, you&apos;ll see it here — with evidence. When
              it recovers, you&apos;ll see that too. The goal is simple:{" "}
              <strong className="text-foreground">
                give developers and teams the data they need to make informed
                decisions about which model to use today
              </strong>
              , not which model was best last month.
            </p>
          </div>
        </div>
      </ScrollReveal>

      {/* Companies */}
      <ScrollReveal>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <a
            href="https://www.trustedsec.com"
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-xl border border-border/50 glass glass-hover p-6 transition-all"
          >
            <div className="flex items-center justify-between mb-3">
              <Shield className="w-8 h-8 text-primary" />
              <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
            </div>
            <h3 className="font-bold text-lg text-foreground mb-2">
              TrustedSec
            </h3>
            <p className="text-sm text-muted-foreground">
              Information security consulting, penetration testing, and
              adversary simulation for organizations worldwide.
            </p>
          </a>

          <a
            href="https://www.binarydefense.com"
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-xl border border-border/50 glass glass-hover p-6 transition-all"
          >
            <div className="flex items-center justify-between mb-3">
              <Globe className="w-8 h-8 text-primary" />
              <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
            </div>
            <h3 className="font-bold text-lg text-foreground mb-2">
              Binary Defense
            </h3>
            <p className="text-sm text-muted-foreground">
              Managed detection and response, threat hunting, and security
              operations for businesses of all sizes.
            </p>
          </a>
        </div>
      </ScrollReveal>

      {/* Acknowledgments */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-6">
          <h3 className="font-bold text-lg text-foreground mb-3">
            Acknowledgments
          </h3>
          <p className="text-sm text-muted-foreground">
            Special thanks to{" "}
            <a
              href="https://x.com/BlasikRandy"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              Randy Blasik
            </a>{" "}
            for inspiring this project and suggesting the idea of independent,
            automated model regression tracking. A special shoutout to{" "}
            <a
              href="https://x.com/edskoudis"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              Ed Skoudis
            </a>{" "}
            for the idea of testing if the model has regressed prior to using
            each day.
          </p>
        </div>
      </ScrollReveal>

      {/* Open Source */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass p-6 text-center">
          <Github className="w-8 h-8 text-foreground mx-auto mb-3" />
          <h3 className="font-bold text-lg text-foreground mb-2">
            Open Source
          </h3>
          <p className="text-sm text-muted-foreground mb-4 max-w-md mx-auto">
            The benchmark suite, test cases, and this website are all open
            source. Inspect the methodology, suggest improvements, or run your
            own benchmarks.
          </p>
          <a
            href="https://github.com/HackingDave/modelregression"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 transition-colors"
          >
            <Github className="w-4 h-4" />
            View on GitHub
          </a>
        </div>
      </ScrollReveal>
    </div>
  );
}
