# Research Basis for Broader Model Regression Sweeps

This note explains why the OpenRouter manifest support and Computer-Use Planning category are included as benchmark infrastructure instead of one-off local experiments.

## Benchmark Design Signals

- Static benchmark scores can overstate model capability when tests are contaminated, under-specified, or divorced from the workflows users actually run. OpenAI's February 2026 note on retiring SWE-bench Verified as its headline coding benchmark argues for broader, more realistic, and frequently refreshed evaluation sets: https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
- NIST's 2026 AI evaluation guidance emphasizes uncertainty, statistical modeling, and richer evaluation tooling rather than single fixed leaderboard numbers: https://www.nist.gov/publications/expanding-ai-evaluation-toolbox-statistical-models
- OpenRouter exposes a model catalog API that makes broad multi-model sweeps practical, but the catalog changes over time. Benchmark runs should therefore use pinned manifests for reproducibility, while a separate generator can refresh the candidate set deliberately: https://openrouter.ai/docs/api/api-reference/models/get-models

## Computer-Use and Agent Benchmarks

Recent agent benchmarks support adding computer-use style tests, but they also show why this project should label the current category as a planning proxy until a live GUI harness exists.

- WindowsWorld evaluates agents on real Windows desktop workflows and highlights the need for observable GUI state and task completion checks: https://arxiv.org/abs/2604.27776
- OpenComputer focuses on computer-use agents with executable desktop environments, reinforcing that true completion requires stateful interaction, not just a text answer: https://arxiv.org/abs/2605.19769
- TerminalWorld and Terminal-Bench show the same pattern in terminal agents: execution environments, logs, and reproducible task state make agent claims testable: https://arxiv.org/abs/2605.22535 and https://arxiv.org/abs/2601.11868

## Cybersecurity and GRC Relevance

The category choices are also motivated by operational failures seen in cybersecurity and compliance workflows: wrong account or tenant context, secret leakage in artifacts, stale deployment health markers, provider-specific evidence drift, and success messages that do not prove real completion. Those failure modes should be generalized into public benchmark tasks without exposing private customer details.

Current 2026 cyber-agent benchmarks point in the same direction:

- Microsoft's CTI-REALM benchmark evaluates end-to-end detection rule generation from threat intelligence, which is closer to real security work than isolated Q&A: https://www.microsoft.com/en-us/security/blog/2026/03/20/cti-realm-a-new-benchmark-for-end-to-end-detection-rule-generation-with-ai-agents/
- Cyber Defense Benchmark evaluates practical cyber defense tasks and highlights the need for task-level measurements across models: https://arxiv.org/abs/2604.19533
- CTFusion studies cybersecurity CTF performance across language models and agents, reinforcing the value of broad model coverage instead of only frontier-provider comparisons: https://arxiv.org/abs/2605.11504

## Practical Implications for This Project

1. Broad sweeps should be model-manifest driven, not live-catalog driven at import time.
2. Open-weight and OpenRouter-hosted models should be first-class benchmark targets, but with explicit cost and concurrency caps.
3. Computer-use tests should evaluate planning, recovery, identity checks, and verification discipline until the project has a live Windows/macOS harness.
4. Cybersecurity/GRC tasks should reward evidence, provenance, tenant/account correctness, secret redaction, and verified final state.
5. Every run should preserve the exact model set that was selected so exported history does not drift when the configured model list changes later.
