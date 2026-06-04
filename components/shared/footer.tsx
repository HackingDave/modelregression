import Link from "next/link";
import { Activity, Github, Twitter } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border/50 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-blue-500 flex items-center justify-center">
                <Activity className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-lg">
                Model<span className="text-gradient">Regression</span>
              </span>
            </div>
            <p className="text-sm text-muted-foreground max-w-md">
              Independent automated benchmarking of frontier AI models. Tracking
              performance regressions so the community knows when models degrade
              — updated 3 times daily.
            </p>
            <div className="flex items-center gap-3 mt-4">
              <a
                href="https://github.com/HackingDave/modelregression"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
              >
                <Github className="w-4 h-4" />
              </a>
              <a
                href="https://twitter.com/HackingDave"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
              >
                <Twitter className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-semibold text-sm text-foreground mb-3">
              Navigate
            </h3>
            <ul className="space-y-2">
              {[
                { href: "/", label: "Dashboard" },
                { href: "/compare", label: "Compare Models" },
                { href: "/outages", label: "Outage Monitor" },
                { href: "/methodology", label: "Methodology" },
              ].map(({ href, label }) => (
                <li key={href}>
                  <Link
                    href={href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-sm text-foreground mb-3">
              About
            </h3>
            <ul className="space-y-2">
              {[
                { href: "/about", label: "About This Project" },
                {
                  href: "https://www.trustedsec.com",
                  label: "TrustedSec",
                  external: true,
                },
                {
                  href: "https://www.binarydefense.com",
                  label: "Binary Defense",
                  external: true,
                },
              ].map(({ href, label, external }) => (
                <li key={href}>
                  {external ? (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {label}
                    </a>
                  ) : (
                    <Link
                      href={href}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-border/50 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            &copy; 2026 ModelRegression.com — Built by David Kennedy
          </p>
          <p className="text-xs text-muted-foreground">
            Benchmarks run 3x daily on DGX Sparks infrastructure
          </p>
        </div>
      </div>
    </footer>
  );
}
