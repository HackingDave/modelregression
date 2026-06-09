#!/usr/bin/env bash
# ============================================================================
# Local test suite for deploy.sh — verifies the two CRITICAL security fixes
# without contacting any server:
#   #1  key-based / non-root auth; password never on the command line
#   #2  host-key verification always on (StrictHostKeyChecking != no)
#
# No dependencies (no bats). Uses PATH-based mocks under ./mocks that capture
# every ssh/sshpass/rsync invocation so we can assert on exactly what would run.
#
#   Run:  bash tests/deploy/run_tests.sh
#   Exit: 0 = all pass, 1 = any failure
# ============================================================================
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
DEPLOY_SH="${DEPLOY_SH:-$REPO/deploy.sh}"   # overridable for negative-control testing
MOCKS="$HERE/mocks"
chmod +x "$MOCKS"/* 2>/dev/null || true

PASS=0; FAIL=0; FAILED=()
ok() { PASS=$((PASS + 1)); printf '  \033[0;32mPASS\033[0m  %s\n' "$1"; }
bad() { FAIL=$((FAIL + 1)); FAILED+=("$1"); printf '  \033[0;31mFAIL\033[0m  %s\n        %s\n' "$1" "${2:-}"; }
has() { case "$1" in *"$2"*) return 0 ;; *) return 1 ;; esac; }

# assert helpers operating on a captured string
want()    { has "$1" "$2" && ok "$3" || bad "$3" "expected to contain: $2"; }
wantnot() { has "$1" "$2" && bad "$3" "should NOT contain: $2" || ok "$3"; }

# --- run deploy.sh's config/auth functions in isolation, capture state ---
# usage: capture <repo_dir> VAR=val VAR=val ...
# prints: SSH_OPTS / AUTH_MODE / RSYNC_SSH / SSHPASS lines; returns its rc
capture() {
    local dir="$1"; shift
    ( cd "$dir" && env "$@" bash -c '
        source "$1"
        load_config; validate_config; build_ssh_opts; setup_auth
        printf "SSH_OPTS=%s\n"   "$SSH_OPTS"
        printf "AUTH_MODE=%s\n"  "${AUTH_MODE:-}"
        printf "RSYNC_SSH=%s\n"  "$RSYNC_SSH"
        printf "SSHPASS=%s\n"    "${SSHPASS:-}"
      ' _ "$DEPLOY_SH" 2>&1 )
}

mkrepo() { local d; d="$(mktemp -d)"; printf '{}\n' > "$d/package.json"; printf '%s' "$d"; }

echo "deploy.sh security test suite"
echo "============================="

# ---------------------------------------------------------------------------
echo ""; echo "[unit] auth + host-key option construction"
# ---------------------------------------------------------------------------

# U1: key auth -> -i present, no sshpass, accept-new (no pin), never =no
repo="$(mkrepo)"; key="$repo/id_test"; : > "$key"
out="$(capture "$repo" PATH="$MOCKS:$PATH" DEPLOY_SERVER_IP=1.2.3.4 DEPLOY_SSH_KEY="$key")"
want    "$out" "AUTH_MODE=key"                  "U1 key mode selected"
want    "$out" "-i $key"                         "U1 key passed via -i"
want    "$out" "RSYNC_SSH=ssh "                  "U1 rsync transport is plain ssh"
wantnot "$out" "sshpass"                         "U1 no sshpass in key mode"
wantnot "$out" "StrictHostKeyChecking=no"        "U1 host-key check not disabled"
want    "$out" "StrictHostKeyChecking=accept-new" "U1 TOFU when no pin"
rm -rf "$repo"

# U2: password auth -> sshpass -e, password NOT in opts, exported via SSHPASS
repo="$(mkrepo)"; PW='s3cr3t-P@ss w0rd!$'
out="$(capture "$repo" PATH="$MOCKS:$PATH" DEPLOY_SERVER_IP=1.2.3.4 DEPLOY_SERVER_PASS="$PW")"
want    "$out" "AUTH_MODE=password"             "U2 password mode selected"
want    "$out" "RSYNC_SSH=sshpass -e ssh"       "U2 rsync transport uses sshpass -e"
want    "$out" "SSHPASS=$PW"                     "U2 password exported via env"
wantnot "$out" "SSH_OPTS=.*$PW"                  "U2 password absent from SSH_OPTS"
# stronger: the password must not appear anywhere in the SSH_OPTS/RSYNC_SSH lines
optline="$(printf '%s\n' "$out" | grep -E '^(SSH_OPTS|RSYNC_SSH)=')"
wantnot "$optline" "$PW"                         "U2 password absent from all ssh argv strings"
wantnot "$out" "StrictHostKeyChecking=no"        "U2 host-key check not disabled"
rm -rf "$repo"

# U3: pinned known_hosts in repo -> strict yes, not accept-new, not no
repo="$(mkrepo)"; key="$repo/id_test"; : > "$key"
printf '1.2.3.4 ssh-ed25519 AAAAfake\n' > "$repo/.deploy_known_hosts"
out="$(capture "$repo" PATH="$MOCKS:$PATH" DEPLOY_SERVER_IP=1.2.3.4 DEPLOY_SSH_KEY="$key")"
want    "$out" "StrictHostKeyChecking=yes"        "U3 strict verification when pinned"
want    "$out" "UserKnownHostsFile=$repo/.deploy_known_hosts" "U3 uses pinned file"
wantnot "$out" "accept-new"                       "U3 not TOFU when pinned"
wantnot "$out" "StrictHostKeyChecking=no"         "U3 host-key check not disabled"
rm -rf "$repo"

# U4: explicit DEPLOY_KNOWN_HOSTS -> strict yes against that file
repo="$(mkrepo)"; key="$repo/id_test"; : > "$key"
kh="$repo/custom_known_hosts"; printf 'host key\n' > "$kh"
out="$(capture "$repo" PATH="$MOCKS:$PATH" DEPLOY_SERVER_IP=1.2.3.4 DEPLOY_SSH_KEY="$key" DEPLOY_KNOWN_HOSTS="$kh")"
want    "$out" "StrictHostKeyChecking=yes"        "U4 strict with explicit known_hosts"
want    "$out" "UserKnownHostsFile=$kh"           "U4 uses explicit known_hosts path"
rm -rf "$repo"

# U5: DEPLOY_SSH_KEY points at missing file -> hard error, exit 1
repo="$(mkrepo)"
out="$(capture "$repo" PATH="$MOCKS:$PATH" DEPLOY_SERVER_IP=1.2.3.4 DEPLOY_SSH_KEY="$repo/nope")"; rc=$?
[ "$rc" -eq 1 ] && ok "U5 missing key file exits 1" || bad "U5 missing key file exits 1" "rc=$rc"
want "$out" "file not found"                      "U5 reports missing key"
rm -rf "$repo"

# U6: no auth configured at all -> hard error, exit 1
repo="$(mkrepo)"
out="$(capture "$repo" PATH="$MOCKS:$PATH" DEPLOY_SERVER_IP=1.2.3.4)"; rc=$?
[ "$rc" -eq 1 ] && ok "U6 no auth exits 1" || bad "U6 no auth exits 1" "rc=$rc"
want "$out" "no SSH auth configured"              "U6 reports missing auth"
rm -rf "$repo"

# U7: missing SERVER_IP -> validate_config exits 1
repo="$(mkrepo)"; key="$repo/id_test"; : > "$key"
out="$(capture "$repo" PATH="$MOCKS:$PATH" DEPLOY_SSH_KEY="$key")"; rc=$?
[ "$rc" -eq 1 ] && ok "U7 missing SERVER_IP exits 1" || bad "U7 missing SERVER_IP exits 1" "rc=$rc"
rm -rf "$repo"

# ---------------------------------------------------------------------------
echo ""; echo "[e2e] full deploy.sh run against mocks"
# ---------------------------------------------------------------------------

# run a full deploy; echoes "<rc>|<logdir>|<outfile>"
run_e2e() {
    local repo="$1"; local logdir="$repo/_logs"; mkdir -p "$logdir"
    ( cd "$repo" && env PATH="$MOCKS:$PATH" MOCK_LOG_DIR="$logdir" \
        bash "$DEPLOY_SH" ) > "$repo/_out" 2>&1
    printf '%s|%s|%s' "$?" "$logdir" "$repo/_out"
}

# E1: key-mode end-to-end
repo="$(mkrepo)"; key="$repo/id_test"; : > "$key"
{ echo "DEPLOY_SERVER_IP=1.2.3.4"; echo "DEPLOY_SSH_KEY=$key"; } > "$repo/.deploy.env"
IFS='|' read -r rc logdir outf <<< "$(run_e2e "$repo")"
[ "$rc" -eq 0 ] && ok "E1 key deploy exits 0" || bad "E1 key deploy exits 0" "rc=$rc: $(tail -3 "$outf")"
grep -q "Deployment Complete" "$outf" && ok "E1 reaches completion" || bad "E1 reaches completion"
[ ! -f "$logdir/sshpass.log" ] && ok "E1 sshpass never invoked in key mode" || bad "E1 sshpass never invoked in key mode"
grep -qaF -- "-i" "$logdir/ssh.argv" && ok "E1 ssh used identity file" || bad "E1 ssh used identity file"
! grep -qaF 'StrictHostKeyChecking=no' "$logdir"/*.argv && ok "E1 never disables host-key check" || bad "E1 never disables host-key check"
grep -qaF 'StrictHostKeyChecking=accept-new' "$logdir/ssh.argv" && ok "E1 host-key verification on (accept-new)" || bad "E1 host-key verification on"
rm -rf "$repo"

# E2: password-mode end-to-end — the password must NEVER appear in any argv
repo="$(mkrepo)"; PW='s3cr3t-P@ss w0rd!$'
# .deploy.env is shell-sourced, so the value must be quoted (as a real one is).
{ echo "DEPLOY_SERVER_IP=1.2.3.4"; printf "DEPLOY_SERVER_PASS='%s'\n" "$PW"; } > "$repo/.deploy.env"
IFS='|' read -r rc logdir outf <<< "$(run_e2e "$repo")"
[ "$rc" -eq 0 ] && ok "E2 password deploy exits 0" || bad "E2 password deploy exits 0" "rc=$rc: $(tail -3 "$outf")"
[ -f "$logdir/sshpass.log" ] && ok "E2 sshpass invoked for password auth" || bad "E2 sshpass invoked for password auth"
grep -qx 'env' "$logdir/sshpass.passmode" 2>/dev/null && ok "E2 password supplied via env, not -p" || bad "E2 password supplied via env, not -p"
if grep -rqaF -- "$PW" "$logdir"; then
    bad "E2 password NEVER in process argv" "found in: $(grep -rlaF -- "$PW" "$logdir" | tr '\n' ' ')"
else
    ok "E2 password NEVER in process argv"
fi
grep -qaF -- "$PW" "$outf" && bad "E2 password not echoed to output" || ok "E2 password not echoed to output"
! grep -qaF 'StrictHostKeyChecking=no' "$logdir"/*.argv && ok "E2 never disables host-key check" || bad "E2 never disables host-key check"
rm -rf "$repo"

# E3: pinned host key end-to-end -> strict yes on the wire
repo="$(mkrepo)"; key="$repo/id_test"; : > "$key"
printf '1.2.3.4 ssh-ed25519 AAAAfake\n' > "$repo/.deploy_known_hosts"
{ echo "DEPLOY_SERVER_IP=1.2.3.4"; echo "DEPLOY_SSH_KEY=$key"; } > "$repo/.deploy.env"
IFS='|' read -r rc logdir outf <<< "$(run_e2e "$repo")"
[ "$rc" -eq 0 ] && ok "E3 pinned deploy exits 0" || bad "E3 pinned deploy exits 0" "rc=$rc: $(tail -3 "$outf")"
grep -qaF 'StrictHostKeyChecking=yes' "$logdir/ssh.argv" && ok "E3 strict verification on the wire" || bad "E3 strict verification on the wire"
! grep -qaF 'accept-new' "$logdir/ssh.argv" && ok "E3 not TOFU when pinned" || bad "E3 not TOFU when pinned"
rm -rf "$repo"

# ---------------------------------------------------------------------------
echo ""
echo "============================="
printf 'Total: %d passed, %d failed\n' "$PASS" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
    printf 'Failed:\n'; printf '  - %s\n' "${FAILED[@]}"
    exit 1
fi
echo "All green."
