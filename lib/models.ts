import { ModelInfo } from "./types";

export const MODELS: ModelInfo[] = [
  {
    id: "claude-opus-4-8",
    provider: "anthropic",
    name: "Claude Opus 4.8",
    slug: "claude-opus-4-8",
    color: "#D97706",
    icon: "brain",
  },
  {
    id: "claude-sonnet-4-6",
    provider: "anthropic",
    name: "Claude Sonnet 4.6",
    slug: "claude-sonnet-4-6",
    color: "#8B5CF6",
    icon: "zap",
  },
  {
    id: "gpt-5-5",
    provider: "openai",
    name: "GPT-5.5",
    slug: "gpt-5-5",
    color: "#10B981",
    icon: "sparkles",
  },
  {
    id: "grok",
    provider: "xai",
    name: "Grok",
    slug: "grok",
    color: "#EF4444",
    icon: "flame",
  },
];

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
  };
  return names[provider] || provider;
}

export function getProviderModels(provider: string): ModelInfo[] {
  return MODELS.filter((m) => m.provider === provider);
}
