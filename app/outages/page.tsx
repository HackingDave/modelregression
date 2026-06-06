import { getOutages } from "@/lib/data";
import { getProviderName } from "@/lib/models";
import { formatDate, formatDateTime, cn } from "@/lib/utils";
import { ScrollReveal } from "@/components/shared/scroll-reveal";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Wifi,
  WifiOff,
} from "lucide-react";

const BASE_PROVIDERS = ["claude", "codex", "agent", "openrouter"];

function getStatusInfo(uptime: number) {
  if (uptime >= 99.9)
    return {
      label: "Operational",
      color: "text-green-400",
      bg: "bg-green-500/10 border-green-500/20",
      icon: CheckCircle2,
    };
  if (uptime >= 99.0)
    return {
      label: "Degraded",
      color: "text-yellow-400",
      bg: "bg-yellow-500/10 border-yellow-500/20",
      icon: AlertTriangle,
    };
  return {
    label: "Issues",
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
    icon: WifiOff,
  };
}

export default function OutagesPage() {
  const outages = getOutages();
  const providers = Array.from(
    new Set([
      ...BASE_PROVIDERS,
      ...Object.keys(outages.uptime),
      ...outages.current.map((o) => o.provider),
      ...outages.history.map((o) => o.provider),
    ])
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Outage Monitor
        </h1>
        <p className="text-muted-foreground">
          Real-time availability tracking for all monitored AI providers.
        </p>
      </div>

      {/* Current Status */}
      <ScrollReveal>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {providers.map((provider) => {
            const uptime7d = outages.uptime[provider]?.["7d"] ?? 100;
            const uptime30d = outages.uptime[provider]?.["30d"] ?? 100;
            const uptime90d = outages.uptime[provider]?.["90d"] ?? 100;
            const status = getStatusInfo(uptime7d);
            const StatusIcon = status.icon;
            const hasCurrentOutage = outages.current.some(
              (o) => o.provider === provider
            );

            return (
              <div
                key={provider}
                className={cn(
                  "rounded-xl border p-5 transition-all",
                  hasCurrentOutage
                    ? "border-red-500/30 bg-red-500/5"
                    : "border-border/50 glass"
                )}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-lg text-foreground">
                    {getProviderName(provider)}
                  </h3>
                  <div
                    className={cn(
                      "flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium",
                      status.bg,
                      status.color
                    )}
                  >
                    <StatusIcon className="w-3.5 h-3.5" />
                    {hasCurrentOutage ? "Outage" : status.label}
                  </div>
                </div>

                <div className="space-y-3">
                  {[
                    { label: "7-day", value: uptime7d },
                    { label: "30-day", value: uptime30d },
                    { label: "90-day", value: uptime90d },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-muted-foreground">{label}</span>
                        <span
                          className={cn(
                            "font-mono font-medium",
                            value >= 99.9
                              ? "text-green-400"
                              : value >= 99
                                ? "text-yellow-400"
                                : "text-red-400"
                          )}
                        >
                          {value.toFixed(2)}%
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all duration-1000",
                            value >= 99.9
                              ? "bg-green-500"
                              : value >= 99
                                ? "bg-yellow-500"
                                : "bg-red-500"
                          )}
                          style={{ width: `${value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </ScrollReveal>

      {/* Current Outages */}
      {outages.current.length > 0 && (
        <ScrollReveal>
          <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-5">
            <div className="flex items-center gap-2 mb-4">
              <WifiOff className="w-5 h-5 text-red-400" />
              <h3 className="font-semibold text-foreground">
                Active Outages
              </h3>
            </div>
            <div className="space-y-3">
              {outages.current.map((outage) => (
                <div
                  key={outage.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-red-500/10 border border-red-500/20"
                >
                  <div>
                    <span className="font-medium text-sm text-foreground">
                      {getProviderName(outage.provider)}
                    </span>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {outage.errorType}: {outage.errorMessage}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono text-red-400">
                      Started {formatDateTime(outage.startedAt)}
                    </span>
                    <p className="text-[10px] text-muted-foreground">
                      {outage.checkCount} consecutive failures
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </ScrollReveal>
      )}

      {/* Outage History */}
      <ScrollReveal>
        <div className="rounded-xl border border-border/50 glass overflow-hidden">
          <div className="p-5 border-b border-border/50">
            <h3 className="font-semibold text-foreground">
              Outage History
            </h3>
          </div>

          {outages.history.length === 0 ? (
            <div className="p-8 text-center">
              <Wifi className="w-8 h-8 text-green-400 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                No outages recorded in the monitoring period.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border/30">
                    <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-4">
                      Provider
                    </th>
                    <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-3">
                      Started
                    </th>
                    <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-3">
                      Ended
                    </th>
                    <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-3">
                      Duration
                    </th>
                    <th className="text-left text-[11px] font-medium text-muted-foreground py-3 px-3">
                      Error
                    </th>
                    <th className="text-center text-[11px] font-medium text-muted-foreground py-3 px-3">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {outages.history.map((outage) => {
                    const start = new Date(outage.startedAt).getTime();
                    const end = outage.endedAt
                      ? new Date(outage.endedAt).getTime()
                      : Date.now();
                    const durationMin = Math.round((end - start) / 60000);

                    return (
                      <tr
                        key={outage.id}
                        className="border-b border-border/20 hover:bg-muted/10"
                      >
                        <td className="py-3 px-4 text-sm font-medium text-foreground">
                          {getProviderName(outage.provider)}
                        </td>
                        <td className="py-3 px-3 text-xs font-mono text-muted-foreground">
                          {formatDateTime(outage.startedAt)}
                        </td>
                        <td className="py-3 px-3 text-xs font-mono text-muted-foreground">
                          {outage.endedAt
                            ? formatDateTime(outage.endedAt)
                            : "Ongoing"}
                        </td>
                        <td className="py-3 px-3 text-xs font-mono text-muted-foreground">
                          {durationMin}m
                        </td>
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            {outage.httpStatus && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-red-500/10 text-red-400 border border-red-500/20">
                                {outage.httpStatus}
                              </span>
                            )}
                            <span className="text-xs text-muted-foreground">
                              {outage.errorMessage}
                            </span>
                          </div>
                        </td>
                        <td className="text-center py-3 px-3">
                          {outage.endedAt ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                              <CheckCircle2 className="w-3 h-3" />
                              Resolved
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-red-500/10 text-red-400 border border-red-500/20">
                              <Clock className="w-3 h-3" />
                              Active
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </ScrollReveal>
    </div>
  );
}
