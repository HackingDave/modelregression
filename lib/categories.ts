import { CategoryInfo } from "./types";

export const CATEGORIES: CategoryInfo[] = [
  {
    id: "long-reasoning",
    name: "Long Reasoning",
    slug: "long-reasoning",
    description:
      "Multi-step logic puzzles, legal reasoning chains, and mathematical proofs that test sustained analytical thinking.",
    icon: "brain",
    weight: 1.0,
  },
  {
    id: "coding-tasks",
    name: "Coding Tasks",
    slug: "coding-tasks",
    description:
      "Implement data structures, REST APIs, and algorithmic challenges from specifications.",
    icon: "code",
    weight: 1.2,
  },
  {
    id: "bug-fixes",
    name: "Bug Fixes",
    slug: "bug-fixes",
    description:
      "Identify and fix subtle bugs including off-by-one errors, race conditions, and memory leaks.",
    icon: "bug",
    weight: 1.2,
  },
  {
    id: "feature-implementation",
    name: "Feature Implementation",
    slug: "feature-implementation",
    description:
      "Add search/filter, rate limiting, pagination, and other features to existing codebases.",
    icon: "puzzle",
    weight: 1.0,
  },
  {
    id: "code-thoroughness",
    name: "Code Thoroughness",
    slug: "code-thoroughness",
    description:
      "Error handling completeness, input validation depth, and test generation quality.",
    icon: "shield-check",
    weight: 0.9,
  },
  {
    id: "bug-introduction-rate",
    name: "Bug Introduction Rate",
    slug: "bug-introduction-rate",
    description:
      "Modify existing code, refactor safely, and add features without breaking existing functionality.",
    icon: "alert-triangle",
    weight: 1.1,
  },
  {
    id: "security-awareness",
    name: "Security Awareness",
    slug: "security-awareness",
    description:
      "SQL injection prevention, vulnerability identification, and secure file handling practices.",
    icon: "lock",
    weight: 1.1,
  },
  {
    id: "instruction-following",
    name: "Instruction Following",
    slug: "instruction-following",
    description:
      "Format constraints, multi-constraint outputs, and adherence to negative instructions.",
    icon: "list-checks",
    weight: 0.8,
  },
  {
    id: "code-quality",
    name: "Code Quality",
    slug: "code-quality",
    description:
      "Clean code standards, readable complex logic, and well-designed API interfaces.",
    icon: "star",
    weight: 0.9,
  },
  {
    id: "performance-efficiency",
    name: "Performance & Efficiency",
    slug: "performance-efficiency",
    description:
      "Algorithm optimization, memory-efficient processing, and database query optimization.",
    icon: "gauge",
    weight: 1.0,
  },
];

export function getCategory(id: string): CategoryInfo | undefined {
  return CATEGORIES.find((c) => c.id === id);
}

export function getCategoryBySlug(slug: string): CategoryInfo | undefined {
  return CATEGORIES.find((c) => c.slug === slug);
}
