#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run_benchmarks.sh  --  Cron entry point for ModelRegression benchmark runs
#
# Runs the benchmark suite, exports JSON data for the website, rebuilds the
# Next.js static site, and deploys it.  All output is logged to a timestamped
# file under benchmark/logs/.
#
# Crontab example (three runs per day, Eastern Time):
#   0  6 * * * /home/hackingdave/projects/modelregression/benchmark/run_benchmarks.sh
#   0 12 * * * /home/hackingdave/projects/modelregression/benchmark/run_benchmarks.sh
#   0 22 * * * /home/hackingdave/projects/modelregression/benchmark/run_benchmarks.sh
# ---------------------------------------------------------------------------
set -euo pipefail

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
# Determine schedule based on current Eastern Time hour
#   morning   = 00:00 - 10:59 ET
#   afternoon = 11:00 - 16:59 ET
#   night     = 17:00 - 23:59 ET
# ---------------------------------------------------------------------------
HOUR=$(TZ="America/New_York" date +%H)
if [ "$HOUR" -lt 11 ]; then
    SCHEDULE="morning"
elif [ "$HOUR" -lt 17 ]; then
    SCHEDULE="afternoon"
else
    SCHEDULE="night"
fi
echo "Schedule: $SCHEDULE  (ET hour: $HOUR)"

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
