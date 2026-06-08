#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run_benchmarks.sh  --  Cron entry point for ModelRegression benchmark runs
#
# Runs the benchmark suite, exports JSON data for the website, rebuilds the
# Next.js static site, and deploys it.  All output is logged to a timestamped
# file under benchmark/logs/.
#
# Crontab example (once daily at 3am ET):
#   0  3 * * * /home/hackingdave/projects/modelregression/benchmark/run_benchmarks.sh
# ---------------------------------------------------------------------------
set -euo pipefail

# ---------------------------------------------------------------------------
# PATH — cron runs with a minimal PATH; add dirs where CLI tools live
# ---------------------------------------------------------------------------
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:/usr/local/bin:$PATH"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_DIR="/home/hackingdave/projects/modelregression"
BENCHMARK_DIR="$PROJECT_DIR/benchmark"
LOG_DIR="$BENCHMARK_DIR/logs"
VENV_DIR="$BENCHMARK_DIR/.venv"

# ---------------------------------------------------------------------------
# Logging -- every run gets its own timestamped log file
# ---------------------------------------------------------------------------
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/run_${TIMESTAMP}.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo "  ModelRegression Benchmark Run"
echo "  Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "========================================"

# ---------------------------------------------------------------------------
# Schedule label — single daily run
# ---------------------------------------------------------------------------
SCHEDULE="daily"
echo "Schedule: $SCHEDULE"

# ---------------------------------------------------------------------------
# Activate Python virtual environment
# ---------------------------------------------------------------------------
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "ERROR: Virtual environment not found at $VENV_DIR"
    echo "Run: python3 -m venv $VENV_DIR && $VENV_DIR/bin/pip install -r $BENCHMARK_DIR/requirements.txt"
    exit 1
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo "Python: $(python --version)  ($(which python))"

# ---------------------------------------------------------------------------
# Step 0: Auto-update CLI tools (claude, codex, agent)
# ---------------------------------------------------------------------------
echo ""
echo "--- Step 0: Updating CLI tools ---"

if command -v claude &>/dev/null; then
    echo "Updating Claude Code..."
    claude update --yes 2>&1 || echo "  (claude update skipped or already latest)"
else
    echo "  WARNING: claude CLI not found"
fi

if command -v codex &>/dev/null; then
    echo "Updating Codex..."
    codex update 2>&1 || echo "  (codex update skipped or already latest)"
else
    echo "  WARNING: codex CLI not found"
fi

if command -v gemini &>/dev/null; then
    echo "Updating Gemini..."
    npm update -g @google/gemini-cli 2>&1 || echo "  (gemini update skipped or already latest)"
else
    echo "  WARNING: gemini CLI not found"
fi

if command -v agent &>/dev/null; then
    echo "Updating Grok Agent..."
    agent update 2>&1 || echo "  (agent update skipped or already latest)"
else
    echo "  WARNING: agent CLI not found"
fi

echo "CLI tools updated."

# ---------------------------------------------------------------------------
# Step 1: Run benchmarks
# ---------------------------------------------------------------------------
echo ""
echo "--- Step 1: Running benchmarks ---"
cd "$BENCHMARK_DIR"
python runner.py --schedule "$SCHEDULE"
echo "Benchmarks completed."

# ---------------------------------------------------------------------------
# Step 2: Export JSON data for the website
# ---------------------------------------------------------------------------
echo ""
echo "--- Step 2: Exporting JSON data ---"
python export_json.py --output "$PROJECT_DIR/public/data"
echo "JSON export completed."

# ---------------------------------------------------------------------------
# Step 3: Build the Next.js site
# ---------------------------------------------------------------------------
echo ""
echo "--- Step 3: Building website ---"
cd "$PROJECT_DIR"
npm run build
echo "Build completed."

# ---------------------------------------------------------------------------
# Step 4: Deploy
# ---------------------------------------------------------------------------
echo ""
echo "--- Step 4: Deploying ---"
bash deploy.sh
echo "Deploy completed."

# ---------------------------------------------------------------------------
# Cleanup: remove log files older than 30 days
# ---------------------------------------------------------------------------
echo ""
echo "--- Cleanup ---"
DELETED=$(find "$LOG_DIR" -name "run_*.log" -mtime +30 -delete -print | wc -l)
echo "Removed $DELETED old log file(s)."

echo ""
echo "========================================"
echo "  Benchmark Run Complete"
echo "  Finished: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "========================================"
