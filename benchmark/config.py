"""
Configuration for ModelRegression benchmark engine.

Defines all models, categories, tests, and API settings.
"""

import os

# ---------------------------------------------------------------------------
# API keys (loaded from environment)
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "benchmarks.db")

# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------
MODELS = [
    {
        "id": "claude-opus-4-8",
        "provider": "anthropic",
        "name": "Claude Opus 4.8",
        "slug": "claude-opus-4-8",
        "api_model": "claude-opus-4-8-20260401",
        "color": "#D97706",
        "icon": "brain",
        "is_active": True,
        "extra_params": {},
    },
    {
        "id": "claude-sonnet-4-6",
        "provider": "anthropic",
        "name": "Claude Sonnet 4.6",
        "slug": "claude-sonnet-4-6",
        "api_model": "claude-sonnet-4-6-20260301",
        "color": "#8B5CF6",
        "icon": "zap",
        "is_active": True,
        "extra_params": {},
    },
    {
        "id": "gpt-5-5",
        "provider": "openai",
        "name": "GPT-5.5",
        "slug": "gpt-5-5",
        "api_model": "gpt-5.5",
        "color": "#10B981",
        "icon": "sparkles",
        "is_active": True,
        "extra_params": {},
    },
    {
        "id": "o3",
        "provider": "openai",
        "name": "O3",
        "slug": "o3",
        "api_model": "o3",
        "color": "#3B82F6",
        "icon": "cpu",
        "is_active": True,
        "extra_params": {"reasoning_effort": "high"},
    },
    {
        "id": "grok",
        "provider": "xai",
        "name": "Grok",
        "slug": "grok",
        "api_model": "grok-3",
        "color": "#EF4444",
        "icon": "flame",
        "is_active": True,
        "extra_params": {},
        "base_url": "https://api.x.ai/v1",
    },
]

# ---------------------------------------------------------------------------
# Category definitions (all weights equal at 1)
# ---------------------------------------------------------------------------
CATEGORIES = [
    {
        "id": "long-reasoning",
        "name": "Long Reasoning",
        "slug": "long-reasoning",
        "description": "Multi-step logic puzzles, extended chain-of-thought, and complex analytical reasoning tasks requiring sustained coherence over many steps.",
        "icon": "brain",
        "weight": 1,
        "sort_order": 1,
    },
    {
        "id": "coding-tasks",
        "name": "Coding Tasks",
        "slug": "coding-tasks",
        "description": "General programming challenges including algorithm implementation, data structure design, and system architecture tasks.",
        "icon": "code",
        "weight": 1,
        "sort_order": 2,
    },
    {
        "id": "bug-fixes",
        "name": "Bug Fixes",
        "slug": "bug-fixes",
        "description": "Identify and fix bugs in existing codebases, including race conditions, off-by-one errors, and logic flaws.",
        "icon": "bug",
        "weight": 1,
        "sort_order": 3,
    },
    {
        "id": "feature-implementation",
        "name": "Feature Implementation",
        "slug": "feature-implementation",
        "description": "End-to-end feature implementation from spec, including tests, error handling, and documentation.",
        "icon": "rocket",
        "weight": 1,
        "sort_order": 4,
    },
    {
        "id": "code-thoroughness",
        "name": "Code Thoroughness",
        "slug": "code-thoroughness",
        "description": "Evaluates completeness of generated code: edge case handling, input validation, error paths, and test coverage.",
        "icon": "shield-check",
        "weight": 1,
        "sort_order": 5,
    },
    {
        "id": "bug-introduction-rate",
        "name": "Bug Introduction Rate",
        "slug": "bug-introduction-rate",
        "description": "Measures how often the model introduces new bugs while writing or modifying code. Lower is better (inverted for scoring).",
        "icon": "alert-triangle",
        "weight": 1,
        "sort_order": 6,
    },
    {
        "id": "security-awareness",
        "name": "Security Awareness",
        "slug": "security-awareness",
        "description": "Tests whether the model proactively identifies and avoids security vulnerabilities like injection, XSS, and insecure defaults.",
        "icon": "lock",
        "weight": 1,
        "sort_order": 7,
    },
    {
        "id": "instruction-following",
        "name": "Instruction Following",
        "slug": "instruction-following",
        "description": "Measures how closely the model adheres to explicit constraints in the prompt, including formatting, language, and output structure.",
        "icon": "list-checks",
        "weight": 1,
        "sort_order": 8,
    },
    {
        "id": "code-quality",
        "name": "Code Quality",
        "slug": "code-quality",
        "description": "Evaluates readability, idiomatic patterns, naming conventions, and adherence to language best practices.",
        "icon": "star",
        "weight": 1,
        "sort_order": 9,
    },
    {
        "id": "performance-efficiency",
        "name": "Performance Efficiency",
        "slug": "performance-efficiency",
        "description": "Tests whether generated code uses efficient algorithms and avoids unnecessary computation, memory allocation, and I/O.",
        "icon": "gauge",
        "weight": 1,
        "sort_order": 10,
    },
]

# ---------------------------------------------------------------------------
# Test definitions (3 per category = 30 total)
# ---------------------------------------------------------------------------
TESTS = [
    # Long Reasoning
    {
        "id": "lr-1",
        "category_id": "long-reasoning",
        "name": "Multi-step Logic Puzzle",
        "description": "Complex optimization with 8+ constraints across multiple variables",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "lr-2",
        "category_id": "long-reasoning",
        "name": "Legal Reasoning Chain",
        "description": "Contract dispute analysis requiring multi-party obligation tracking",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "lr-3",
        "category_id": "long-reasoning",
        "name": "Mathematical Proof",
        "description": "Prove divisibility properties using induction and modular arithmetic",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    # Coding Tasks
    {
        "id": "ct-1",
        "category_id": "coding-tasks",
        "name": "Graph Algorithm Implementation",
        "description": "Implement Dijkstra with priority queue and handle edge cases",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "ct-2",
        "category_id": "coding-tasks",
        "name": "REST API Design",
        "description": "Design and implement a paginated REST API with filtering",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "ct-3",
        "category_id": "coding-tasks",
        "name": "Concurrent Data Pipeline",
        "description": "Build a producer-consumer pipeline with backpressure handling",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    # Bug Fixes
    {
        "id": "bf-1",
        "category_id": "bug-fixes",
        "name": "Race Condition Detection",
        "description": "Find and fix a subtle race condition in async queue processing",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "bf-2",
        "category_id": "bug-fixes",
        "name": "Memory Leak Fix",
        "description": "Identify and patch a memory leak caused by unclosed event listeners",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "bf-3",
        "category_id": "bug-fixes",
        "name": "Off-by-One Boundary Fix",
        "description": "Fix pagination logic that skips the last page of results",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    # Feature Implementation
    {
        "id": "fi-1",
        "category_id": "feature-implementation",
        "name": "OAuth2 Integration",
        "description": "Implement complete OAuth2 flow with PKCE and token refresh",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "fi-2",
        "category_id": "feature-implementation",
        "name": "Search Autocomplete",
        "description": "Build debounced search with trie-based suggestions and highlighting",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "fi-3",
        "category_id": "feature-implementation",
        "name": "Webhook System",
        "description": "Design webhook delivery with retry logic and signature verification",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    # Code Thoroughness
    {
        "id": "cth-1",
        "category_id": "code-thoroughness",
        "name": "Edge Case Coverage",
        "description": "Generate code handling null, empty, unicode, and overflow inputs",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "cth-2",
        "category_id": "code-thoroughness",
        "name": "Error Path Completeness",
        "description": "Ensure all failure modes have proper error handling and logging",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "cth-3",
        "category_id": "code-thoroughness",
        "name": "Test Suite Completeness",
        "description": "Generate tests covering happy path, edge cases, and integration",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    # Bug Introduction Rate
    {
        "id": "bi-1",
        "category_id": "bug-introduction-rate",
        "name": "Refactor Without Regression",
        "description": "Refactor a function without introducing new failures in existing tests",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "bi-2",
        "category_id": "bug-introduction-rate",
        "name": "Merge Conflict Resolution",
        "description": "Resolve merge conflicts without introducing semantic errors",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "bi-3",
        "category_id": "bug-introduction-rate",
        "name": "Dependency Upgrade Safety",
        "description": "Upgrade a dependency and adapt code without breaking changes",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    # Security Awareness
    {
        "id": "sa-1",
        "category_id": "security-awareness",
        "name": "SQL Injection Prevention",
        "description": "Build a query layer that properly parameterizes all user input",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "sa-2",
        "category_id": "security-awareness",
        "name": "XSS Mitigation",
        "description": "Render user-generated content without introducing XSS vectors",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "sa-3",
        "category_id": "security-awareness",
        "name": "Secret Management",
        "description": "Implement config loading that never logs or exposes secrets",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    # Instruction Following
    {
        "id": "if-1",
        "category_id": "instruction-following",
        "name": "Structured Output Compliance",
        "description": "Produce JSON matching an exact schema with no extra fields",
        "eval_type": "exact_match",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "if-2",
        "category_id": "instruction-following",
        "name": "Constraint Adherence",
        "description": "Follow explicit constraints like max line length and naming conventions",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "if-3",
        "category_id": "instruction-following",
        "name": "Multi-step Instruction Chain",
        "description": "Execute a 6-step instruction sequence without skipping or reordering",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    # Code Quality
    {
        "id": "cq-1",
        "category_id": "code-quality",
        "name": "Idiomatic Python",
        "description": "Write Pythonic code using generators, comprehensions, and context managers",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "cq-2",
        "category_id": "code-quality",
        "name": "TypeScript Best Practices",
        "description": "Use strict types, discriminated unions, and proper error narrowing",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "cq-3",
        "category_id": "code-quality",
        "name": "Clean Architecture Patterns",
        "description": "Implement repository pattern with proper dependency inversion",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
    # Performance Efficiency
    {
        "id": "pe-1",
        "category_id": "performance-efficiency",
        "name": "Algorithm Complexity",
        "description": "Solve a problem in O(n log n) instead of naive O(n^2)",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "pe-2",
        "category_id": "performance-efficiency",
        "name": "Memory-efficient Processing",
        "description": "Process a large file using streaming instead of loading into memory",
        "eval_type": "sandbox_exec",
        "max_score": 100,
        "version": 1,
    },
    {
        "id": "pe-3",
        "category_id": "performance-efficiency",
        "name": "Query Optimization",
        "description": "Write database queries that use indexes and avoid N+1 patterns",
        "eval_type": "llm_judge",
        "max_score": 100,
        "version": 1,
    },
]

# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def get_model_by_id(model_id: str) -> dict | None:
    """Look up a model config dict by its id."""
    for m in MODELS:
        if m["id"] == model_id:
            return m
    return None


def get_category_by_id(cat_id: str) -> dict | None:
    """Look up a category config dict by its id."""
    for c in CATEGORIES:
        if c["id"] == cat_id:
            return c
    return None


def get_tests_for_category(cat_id: str) -> list[dict]:
    """Return list of test dicts for a category."""
    return [t for t in TESTS if t["category_id"] == cat_id]


# Map from internal test IDs (cth-*) to the slug used in JSON output (th-*)
# The seed data uses th-1/2/3 for code-thoroughness rather than cth-1/2/3
TEST_ID_TO_DISPLAY = {
    "cth-1": "th-1",
    "cth-2": "th-2",
    "cth-3": "th-3",
}


def display_test_id(test_id: str) -> str:
    """Return the display/JSON test id (e.g. cth-1 -> th-1)."""
    return TEST_ID_TO_DISPLAY.get(test_id, test_id)
