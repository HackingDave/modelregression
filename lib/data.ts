import fs from "fs";
import path from "path";
import type {
  LatestRun,
  Synopsis,
  ModelDetail,
  CategoryDetail,
  TrendData,
  RegressionData,
  OutageData,
  EvidenceData,
} from "./types";

function loadJSON<T>(filePath: string): T {
  const fullPath = path.join(process.cwd(), "public", "data", filePath);
  const raw = fs.readFileSync(fullPath, "utf-8");
  return JSON.parse(raw) as T;
}

export function getLatestRun(): LatestRun {
  return loadJSON<LatestRun>("latest.json");
}

export function getSynopsis(): Synopsis {
  return loadJSON<Synopsis>("synopsis.json");
}

export function getModelDetail(slug: string): ModelDetail {
  return loadJSON<ModelDetail>(`models/${slug}.json`);
}

export function getCategoryDetail(slug: string): CategoryDetail {
  return loadJSON<CategoryDetail>(`categories/${slug}.json`);
}

export function getTrends(period: string): TrendData {
  return loadJSON<TrendData>(`trends/${period}.json`);
}

export function getRegressions(): RegressionData {
  return loadJSON<RegressionData>("regressions.json");
}

export function getOutages(): OutageData {
  return loadJSON<OutageData>("outages.json");
}

export function getEvidence(runId: string, testId: string): EvidenceData {
  return loadJSON<EvidenceData>(`evidence/${runId}/${testId}.json`);
}

export function getAllModelSlugs(): string[] {
  const dir = path.join(process.cwd(), "public", "data", "models");
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""));
}

export function getAllCategorySlugs(): string[] {
  const dir = path.join(process.cwd(), "public", "data", "categories");
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""));
}

export function getAllEvidencePaths(): { runId: string; testId: string }[] {
  const dir = path.join(process.cwd(), "public", "data", "evidence");
  if (!fs.existsSync(dir)) return [];
  const paths: { runId: string; testId: string }[] = [];
  for (const runDir of fs.readdirSync(dir)) {
    const runPath = path.join(dir, runDir);
    if (!fs.statSync(runPath).isDirectory()) continue;
    for (const file of fs.readdirSync(runPath)) {
      if (file.endsWith(".json")) {
        paths.push({ runId: runDir, testId: file.replace(".json", "") });
      }
    }
  }
  return paths;
}
