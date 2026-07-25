import { ModelInfo } from "./types";
import modelCatalog from "@/public/data/model-catalog.json";

export const MODELS: ModelInfo[] = modelCatalog as ModelInfo[];

export function getModel(id: string): ModelInfo | undefined {
  return MODELS.find((m) => m.id === id);
}

export function getModelBySlug(slug: string): ModelInfo | undefined {
  return MODELS.find((m) => m.slug === slug);
}

export function getProviderName(provider: string): string {
  const names: Record<string, string> = {
    anthropic: "Anthropic",
    openai: "OpenAI",
    xai: "xAI",
    claude: "Anthropic",
    codex: "OpenAI",
    agent: "xAI",
    grok: "xAI",
  };
  return names[provider] || provider;
}

export function getProviderModels(provider: string): ModelInfo[] {
  return MODELS.filter((m) => m.provider === provider);
}
