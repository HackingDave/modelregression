import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number | null | undefined): string {
  if (score == null) return "—";
  return score.toFixed(1);
}

export function formatPercent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export function getScoreColor(score: number | null | undefined): string {
  if (score == null) return "text-muted-foreground";
  if (score >= 90) return "text-score-excellent";
  if (score >= 80) return "text-score-good";
  if (score >= 70) return "text-score-average";
  if (score >= 60) return "text-score-below";
  return "text-score-poor";
}

export function getScoreBg(score: number): string {
  if (score >= 90) return "bg-score-excellent";
  if (score >= 80) return "bg-score-good";
  if (score >= 70) return "bg-score-average";
  if (score >= 60) return "bg-score-below";
  return "bg-score-poor";
}

export function getScoreGlow(score: number): string {
  if (score >= 90) return "shadow-glow-green";
  if (score >= 70) return "";
  return "shadow-glow-red";
}

export function getTrendIcon(change: number): "up" | "down" | "stable" {
  if (change > 2) return "up";
  if (change < -2) return "down";
  return "stable";
}

export function getTrendColor(change: number): string {
  if (change > 2) return "text-score-excellent";
  if (change < -2) return "text-score-poor";
  return "text-yellow-500";
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}
