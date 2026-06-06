# ModelRegression.com

Independent, automated benchmarking of frontier AI coding models. Tracks performance over time so the community knows when models improve — or regress.

**Live site: [modelregression.com](https://modelregression.com)**

## Why This Exists

AI model providers update their models constantly, and sometimes performance degrades without any announcement. ModelRegression runs the same 33 tests against every model daily, scores the results, and surfaces regressions automatically. No vendor self-reporting — just independent, reproducible benchmarks.

## Trust Status

The dashboard now answers the blunt question security teams actually care about:

> Can I trust this model today?

Each model gets a plain-English status:

- **Good** - useful for security review support, with human verification.
- **Watch** - helpful, but do not let it make the final call.
- **Do not trust alone** - keep it away from incident response, risky fixes, and compliance decisions unless a human is driving.

The status is derived from the latest composite score, Security Awareness score, Code Thoroughness score, active regression flags, and the weakest security-awareness evidence from the current run. Every claim links back to receipts.

## What Gets Tested

33 tests across 11 categories, each targeting a different dimension of coding and agentic ability:

| Category | What It Measures |
|---|---|
| Long Reasoning | Multi-step logic, legal reasoning, mathematical proofs |
| Coding Tasks | Algorithm implementation, API design, concurrent pipelines |
| Bug Fixes | Race conditions, memory leaks, off-by-one errors |
| Feature Implementation | OAuth2 flows, search autocomplete, webhook systems |
| Code Thoroughness | Edge case coverage, error handling, test completeness |
| Bug Introduction Rate | Refactoring safety, merge conflicts, dependency upgrades |
| Security Awareness | SQL injection, XSS, secret management |
| Instruction Following | Schema compliance, constraint adherence, multi-step chains |
| Code Quality | Idiomatic Python, TypeScript best practices, clean architecture |
| Performance Efficiency | Algorithm complexity, streaming, query optimization |
| Computer-Use Planning | Windows/macOS GUI state reasoning, recovery planning, and verified-completion discipline |

## Models Tracked

- **Claude Opus 4.8** (Anthropic) — via `claude` CLI
- **Claude Sonnet 4.6** (Anthropic) — via `claude` CLI
- **GPT-5.5** (OpenAI) — via `codex` CLI
- **Grok** (xAI) — via `agent` CLI
- **OpenRouter models** (open-weight/open-source candidates) - opt-in via `OPENROUTER_MODEL_IDS` or a pinned manifest

Default frontier models are tested through their official CLI tools. OpenRouter models are tested through OpenRouter's chat-completions API so the same suite can cover dozens of open-weight and API-hosted models.

See [docs/research-basis.md](docs/research-basis.md) for the benchmark design rationale, including recent 2026 computer-use and cybersecurity benchmark references.

## Architecture

```
                ┌──────────────┐
                │   DGX Sparks │  Runs benchmarks daily (3am ET)
                │   (cron job) │  Python 3.13 + SQLite
                └──────┬───────┘
                       │
            benchmark suite runs 33 tests
            against each model via configured adapters
                       │
                       ▼
                ┌──────────────┐
                │  export_json │  SQLite → static JSON files
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │   Next.js 15 │  Static site generation
                │   + deploy   │  Blue-green deploy to Linode
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │    Linode    │  Nginx reverse proxy + PM2
                │   (prod)    │  modelregression.com
                └──────────────┘
```

### Website Stack

- **Next.js 15** (App Router) with static site generation
- **TailwindCSS** for styling
- **Recharts** for interactive charts
- **Framer Motion** for animations

### Benchmark Engine

- **Python 3.13** orchestrator with parallel test execution
- **SQLite** for storing all results, scores, regressions, and outages
- **LLM-as-judge** evaluation using Claude Sonnet for subjective tests
- **Sandbox execution** for tests with deterministic outputs
- **Regression detection** with configurable thresholds and severity levels
- **Outage monitoring** with pre-flight health checks before each run

## Project Structure

```
modelregression/
├── app/                          # Next.js pages
│   ├── page.tsx                  #   Dashboard
│   ├── models/[slug]/            #   Per-model detail pages
│   ├── categories/[slug]/        #   Per-category detail pages
│   ├── compare/                  #   Side-by-side model comparison
│   ├── evidence/[runId]/[testId] #   Full test evidence (prompts, outputs, scores)
│   ├── outages/                  #   Outage history + uptime
│   ├── methodology/              #   How benchmarks work
│   └── about/                    #   About the project
├── components/                   # React components
│   ├── charts/                   #   Recharts wrappers
│   ├── dashboard/                #   Dashboard-specific components
│   └── shared/                   #   Navbar, footer, animations
├── lib/                          # Types, utilities, data loading
├── public/data/                  # Generated JSON (from benchmark engine)
├── benchmark/                    # Python benchmark suite
│   ├── runner.py                 #   Main orchestrator
│   ├── config.py                 #   Models, categories, test definitions
│   ├── db.py                     #   SQLite schema + queries
│   ├── export_json.py            #   SQLite → JSON exporter
│   ├── scoring.py                #   Score aggregation + composites
│   ├── regression_detector.py    #   Regression detection logic
│   ├── outage_monitor.py         #   Health checks + outage tracking
│   ├── run_benchmarks.sh         #   Cron entry point (full pipeline)
│   └── tests/                    #   Test implementations (33 tests)
│       ├── base.py               #     Base test class
│       ├── long_reasoning.py     #     3 long reasoning tests
│       ├── coding_tasks.py       #     3 coding task tests
│       ├── bug_fixes.py          #     3 bug fix tests
│       └── ...                   #     (11 categories x 3 tests each)
├── config/                       # Nginx configuration
├── deploy.sh                     # Blue-green atomic deployment
└── ecosystem.config.js           # PM2 process configuration
```

## Setup

### Website (Development)

```bash
# Install dependencies
npm install

# Start dev server (port 3002)
npm run dev

# Production build
npm run build
npm start
```

### Benchmark Engine

```bash
cd benchmark

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run benchmarks for all models
python runner.py --schedule daily

# Run benchmarks for a single model
python runner.py --schedule daily --model grok

# Export results to JSON for the website
python export_json.py --output ../public/data
```

### CLI Tool Prerequisites

The benchmark engine calls default frontier models through their official CLI tools. You need these installed and authenticated:

- **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** (`claude`) — for Anthropic models
- **[Codex CLI](https://github.com/openai/codex)** (`codex`) — for OpenAI models
- **[Grok Agent](https://docs.x.ai/docs/grok-agent)** (`agent`) — for xAI models

### OpenRouter Model Sweeps

OpenRouter support is opt-in so daily runs do not suddenly benchmark dozens of additional models or incur unexpected cost. Broad sweeps should be pinned in a manifest first; benchmark runs do not fetch the live OpenRouter catalog during config import.

```powershell
# Controlled OpenRouter run against explicit model IDs
$env:OPENROUTER_API_KEY = "<your key>"
$env:OPENROUTER_MODEL_IDS = "meta-llama/llama-3.3-70b-instruct,qwen/qwen3.7-plus"
py -3 benchmark\runner.py --schedule daily

# Generate and review a broad open-weight candidate manifest
$env:OPENROUTER_API_KEY = "<your key>"
py -3 benchmark\openrouter_manifest.py --limit 50 --output benchmark\manifests\openrouter_models.json

# Run from the pinned manifest
$env:OPENROUTER_MANIFEST = "benchmark\manifests\openrouter_models.json"
py -3 benchmark\runner.py --schedule daily

# Optional: only include OpenRouter :free variants while generating the manifest
py -3 benchmark\openrouter_manifest.py --free-only --limit 50 --output benchmark\manifests\openrouter_models.json
```

The manifest generator currently matches provider/model prefixes such as `meta-llama/`, `mistralai/`, `qwen/`, `deepseek/`, `google/gemma`, `nvidia/`, `microsoft/`, and other open-weight candidate families. Treat these as open-weight candidates until licenses are verified. Override with repeated `--prefix` flags when the catalog changes.

Useful safety controls:

```powershell
$env:OPENROUTER_MAX_MODELS = "50"          # fail fast if the manifest is larger
$env:MAX_PARALLEL_MODELS = "4"             # global model-level workers
$env:OPENROUTER_PARALLEL_TESTS = "1"       # per-OpenRouter-model test workers
```

### OpenRouter Pricing

The JSON export also refreshes `public/data/openrouter-pricing.json` from OpenRouter's model catalog each day. Prices are normalized from OpenRouter's per-token values into dollars per 1M input tokens, dollars per 1M output tokens, and a simple 1M-in + 1M-out blended number for dashboard display.

```powershell
# Standalone refresh if you only want to update the price sheet
py -3 benchmark\openrouter_pricing.py --output public\data\openrouter-pricing.json
```

Negative OpenRouter router sentinel prices are ignored because they do not represent a real per-token price.

### Deployment

Deployment uses a blue-green strategy with zero-downtime swaps:

```bash
# Requires .deploy.env with server credentials (not checked into git)
bash deploy.sh
```

### Automated Daily Runs

The full pipeline (benchmark, export, build, deploy) runs via cron on the DGX:

```
0 3 * * * /path/to/benchmark/run_benchmarks.sh
```

## How Scoring Works

1. Each test produces a raw score (0-100) via sandbox execution, LLM-as-judge, or exact match
2. Scores are averaged per category (3 tests each)
3. Category averages are combined into a composite score (equal weight)
4. Composite scores are ranked across models
5. Regression detection compares against a rolling window of previous runs
6. Regressions are classified by severity: minor (>5% drop), moderate (>10%), major (>20%)

## Contributing

Found a bug? Have an idea for a new test category? Open an issue or submit a PR.

When adding new tests:
1. Create a new test class in `benchmark/tests/` extending `BaseTest`
2. Add the test definition to `benchmark/config.py`
3. The runner and exporter pick it up automatically

## Acknowledgments

- [Randy Blasik](https://x.com/BlasikRandy) for inspiring this project and suggesting independent, automated model regression tracking
- [Ed Skoudis](https://x.com/edskoudis) for the idea of testing if the model has regressed prior to using each day

## License

MIT
