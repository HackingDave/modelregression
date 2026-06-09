# deploy.sh test suite

Local, dependency-free tests for the deployment script's auth and host-key
handling. No server is contacted — `ssh`/`sshpass`/`rsync`/`sleep` are replaced
by mocks under `mocks/` that capture every invocation so the tests can assert on
exactly what would run.

## Run

```bash
bash tests/deploy/run_tests.sh
```

Exit 0 = all pass. Nothing is written outside `mktemp` dirs; your real
`.deploy.env` is never read or modified.

## What it verifies

Two CRITICAL fixes:

- **Host-key verification is always on** — `StrictHostKeyChecking` is `yes`
  (pinned `known_hosts`) or `accept-new` (trust-on-first-use), never `no`.
- **Password never hits the process table** — password auth goes through
  `sshpass -e` (env var `SSHPASS`); the password appears in no command-line
  argv. Key-based auth (`DEPLOY_SSH_KEY`) is preferred and uses no `sshpass`.

Coverage: key vs password auth selection, pinned vs explicit vs TOFU
known_hosts, error paths (missing key, no auth, missing server IP), and two
full mocked end-to-end deploys.

## Negative control

Confirm the suite can actually fail by pointing it at a deliberately
re-vulnerable copy:

```bash
vuln=$(mktemp)
sed -e 's/StrictHostKeyChecking=accept-new/StrictHostKeyChecking=no/' \
    -e 's/sshpass -e ssh \$SSH_OPTS/sshpass -p "$SERVER_PASS" ssh $SSH_OPTS/g' \
    deploy.sh > "$vuln"
DEPLOY_SH="$vuln" bash tests/deploy/run_tests.sh   # must exit non-zero
rm -f "$vuln"
```

## Deploy config (for reference)

`.deploy.env` (gitignored, shell-sourced — quote values):

```bash
DEPLOY_SERVER_IP=1.2.3.4
DEPLOY_SSH_KEY=/home/you/.ssh/deploy_key      # preferred; non-root user ideally
# DEPLOY_SERVER_USER=deploy
# DEPLOY_KNOWN_HOSTS=/path/to/known_hosts     # else ./.deploy_known_hosts, else TOFU
# DEPLOY_SERVER_PASS='...'                    # fallback only; key auth is better
```

Pin the host key once: `ssh-keyscan -p 44444 <ip> > .deploy_known_hosts`.
