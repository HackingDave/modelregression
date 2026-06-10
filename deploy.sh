#!/bin/bash
# ============================================
# ModelRegression.com Deployment Script
# Blue-green atomic deploy to Linode server
# ============================================
#
# Auth (in order of preference):
#   DEPLOY_SSH_KEY    path to a private key -> key-based auth (recommended)
#   DEPLOY_SERVER_PASS  password -> sshpass via env (SSHPASS), never on argv
# Host-key verification (always on):
#   DEPLOY_KNOWN_HOSTS  path to a pinned known_hosts file (strict)
#   else ./.deploy_known_hosts if non-empty (strict)
#   else trust-on-first-use (accept-new) and record the key for next time
#
# Logic lives in functions so the local test suite (tests/deploy/) can source
# and exercise it without contacting a server. main() runs only on execution.

set -u

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

load_config() {
    if [ -f ".deploy.env" ]; then
        # shellcheck disable=SC1091
        source .deploy.env
    fi
    SERVER_IP="${DEPLOY_SERVER_IP:-}"
    SERVER_PORT="${DEPLOY_SERVER_PORT:-44444}"
    SERVER_USER="${DEPLOY_SERVER_USER:-root}"
    SERVER_PASS="${DEPLOY_SERVER_PASS:-}"
    SSH_KEY="${DEPLOY_SSH_KEY:-}"
    KNOWN_HOSTS="${DEPLOY_KNOWN_HOSTS:-}"
    REMOTE_PATH="${DEPLOY_REMOTE_PATH:-/var/www/modelregression}"
    LOCAL_PATH="${DEPLOY_LOCAL_PATH:-$(pwd)}"
    APP_NAME="modelregression"
}

validate_config() {
    if [ -z "$SERVER_IP" ]; then
        echo -e "${RED}Error: Missing required deployment config (DEPLOY_SERVER_IP).${NC}" >&2
        exit 1
    fi
}

# Build SSH_OPTS with host-key verification ALWAYS enabled (fix: no
# StrictHostKeyChecking=no). Pinned known_hosts -> strict; otherwise
# trust-on-first-use, which records the key and verifies it on every later run.
build_ssh_opts() {
    SSH_OPTS="-p $SERVER_PORT -o ConnectTimeout=10"
REMOTE_PARENT="$(dirname "$REMOTE_PATH")"
REMOTE_BASENAME="$(basename "$REMOTE_PATH")"
TIMESTAMP="$(date +%Y%m%d%H%M%S)"
REMOTE_RELEASE_PATH="${REMOTE_PARENT}/${REMOTE_BASENAME}_release_${TIMESTAMP}"
REMOTE_BACKUP_PATH="${REMOTE_PARENT}/${REMOTE_BASENAME}_backup_previous"
APP_HEALTH_URL="http://127.0.0.1:3002"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ModelRegression.com Deploy${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Prepare staged release directory on server
echo -e "${YELLOW}Preparing staged release directory...${NC}"
ssh_cmd "
    set -e
    rm -rf '$REMOTE_RELEASE_PATH'
    mkdir -p '$REMOTE_RELEASE_PATH'
"
echo -e "${GREEN}Stage prepared${NC}"

# Sync project files (excluding dev/benchmark files)
echo -e "${YELLOW}Syncing files to staged release...${NC}"
rsync -avz --progress \
    -e "$RSYNC_SSH" \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude '.env' \
    --exclude '.env.local' \
    --exclude '.deploy.env' \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '.pytest_cache' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'benchmark' \
    --exclude 'dogfood-output' \
    --exclude '.DS_Store' \
    --exclude '*.log' \
    --exclude 'tsconfig.tsbuildinfo' \
    --exclude 'out' \
    "$LOCAL_PATH/" "$SERVER_USER@$SERVER_IP:$REMOTE_RELEASE_PATH/"

if [ $? -ne 0 ]; then
    echo -e "${RED}File sync failed.${NC}"
    ssh_cmd "rm -rf '$REMOTE_RELEASE_PATH'"
    exit 1
fi
echo -e "${GREEN}Files synced successfully${NC}"

# Install dependencies on server
echo -e "${YELLOW}Installing dependencies...${NC}"
ssh_cmd "set -e; cd '$REMOTE_RELEASE_PATH' && npm install --legacy-peer-deps"
if [ $? -ne 0 ]; then
    echo -e "${RED}Dependency install failed.${NC}"
    ssh_cmd "rm -rf '$REMOTE_RELEASE_PATH'"
    exit 1
fi

    local kh_file=""
    if [ -n "$KNOWN_HOSTS" ]; then
        kh_file="$KNOWN_HOSTS"
    else
        kh_file="$LOCAL_PATH/.deploy_known_hosts"
    fi

    if [ -s "$kh_file" ]; then
        SSH_OPTS="$SSH_OPTS -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$kh_file"
    else
        SSH_OPTS="$SSH_OPTS -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=$kh_file"
        echo -e "${YELLOW}Warning: host key not pinned; using accept-new (trust-on-first-use).${NC}" >&2
        echo -e "${YELLOW}  Pin it: ssh-keyscan -p $SERVER_PORT $SERVER_IP > .deploy_known_hosts${NC}" >&2
    fi
}

# Select auth method and define ssh_cmd()/RSYNC_SSH. Key auth is preferred;
# password auth is passed via the SSHPASS env var (sshpass -e), never as a
# command-line argument (fix: no cleartext password in the process table).
setup_auth() {
    if [ -n "$SSH_KEY" ]; then
        if [ ! -f "$SSH_KEY" ]; then
            echo -e "${RED}Error: DEPLOY_SSH_KEY set but file not found: $SSH_KEY${NC}" >&2
            exit 1
        fi
        SSH_OPTS="$SSH_OPTS -i $SSH_KEY -o IdentitiesOnly=yes -o PreferredAuthentications=publickey"
        AUTH_MODE="key"
        # shellcheck disable=SC2086
        ssh_cmd() { ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$1"; }
        RSYNC_SSH="ssh $SSH_OPTS"
    elif [ -n "$SERVER_PASS" ]; then
        if ! command -v sshpass >/dev/null 2>&1; then
            echo -e "${RED}Error: sshpass required for password auth (prefer DEPLOY_SSH_KEY).${NC}" >&2
            exit 1
        fi
        echo -e "${YELLOW}Warning: password auth in use. Prefer key auth via DEPLOY_SSH_KEY.${NC}" >&2
        if [ "$SERVER_USER" = "root" ]; then
            echo -e "${YELLOW}Warning: deploying as root. Prefer a non-root deploy user with scoped sudo.${NC}" >&2
        fi
        AUTH_MODE="password"
        export SSHPASS="$SERVER_PASS"   # read by sshpass -e from env, never argv
        # shellcheck disable=SC2086
        ssh_cmd() { sshpass -e ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$1"; }
        RSYNC_SSH="sshpass -e ssh $SSH_OPTS"
    else
        echo -e "${RED}Error: no SSH auth configured. Set DEPLOY_SSH_KEY (preferred) or DEPLOY_SERVER_PASS.${NC}" >&2
        exit 1
    fi
}

main() {
    load_config
    validate_config
    build_ssh_opts
    setup_auth

    REMOTE_PARENT="$(dirname "$REMOTE_PATH")"
    REMOTE_BASENAME="$(basename "$REMOTE_PATH")"
    TIMESTAMP="$(date +%Y%m%d%H%M%S)"
    REMOTE_RELEASE_PATH="${REMOTE_PARENT}/${REMOTE_BASENAME}_release_${TIMESTAMP}"
    REMOTE_BACKUP_PATH="${REMOTE_PARENT}/${REMOTE_BASENAME}_backup_previous"
    APP_HEALTH_URL="http://127.0.0.1:3002"

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  ModelRegression.com Deploy${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # Prepare staged release directory on server
    echo -e "${YELLOW}Preparing staged release directory...${NC}"
    ssh_cmd "
        set -e
        rm -rf '$REMOTE_RELEASE_PATH'
        mkdir -p '$REMOTE_RELEASE_PATH'
    "
    echo -e "${GREEN}Stage prepared${NC}"

    # Sync project files (excluding dev/benchmark files)
    echo -e "${YELLOW}Syncing files to staged release...${NC}"
    rsync -avz --progress \
        -e "$RSYNC_SSH" \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude '.env' \
        --exclude '.env.local' \
        --exclude '.deploy.env' \
        --exclude '.git' \
        --exclude 'benchmark' \
        --exclude 'dogfood-output' \
        --exclude '.DS_Store' \
        --exclude '*.log' \
        --exclude 'tsconfig.tsbuildinfo' \
        --exclude 'out' \
        "$LOCAL_PATH/" "$SERVER_USER@$SERVER_IP:$REMOTE_RELEASE_PATH/"

    if [ $? -ne 0 ]; then
        echo -e "${RED}File sync failed.${NC}"
        ssh_cmd "rm -rf '$REMOTE_RELEASE_PATH'"
        exit 1
    fi
    echo -e "${GREEN}Files synced successfully${NC}"

    # Install dependencies on server
    echo -e "${YELLOW}Installing dependencies...${NC}"
    ssh_cmd "set -e; cd '$REMOTE_RELEASE_PATH' && npm install --legacy-peer-deps"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Dependency install failed.${NC}"
        ssh_cmd "rm -rf '$REMOTE_RELEASE_PATH'"
        exit 1
    fi

    # Build on server
    echo -e "${YELLOW}Building production release...${NC}"
    ssh_cmd "set -e; cd '$REMOTE_RELEASE_PATH' && npm run build"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Remote build failed.${NC}"
        ssh_cmd "rm -rf '$REMOTE_RELEASE_PATH'"
        exit 1
    fi

    # Verify build
    echo -e "${YELLOW}Verifying build artifacts...${NC}"
    ssh_cmd "
        set -e
        cd '$REMOTE_RELEASE_PATH'
        test -f .next/BUILD_ID
        test -f .next/build-manifest.json
        test -d .next/server
        test -d .next/static
    "
    if [ $? -ne 0 ]; then
        echo -e "${RED}Build verification failed.${NC}"
        ssh_cmd "rm -rf '$REMOTE_RELEASE_PATH'"
        exit 1
    fi
    echo -e "${GREEN}Build successful${NC}"

    # Atomic swap
    echo -e "${YELLOW}Swapping staged release into production...${NC}"
    ssh_cmd "
        set -e
        rm -rf '$REMOTE_BACKUP_PATH'
        if [ -d '$REMOTE_PATH' ]; then
            mv '$REMOTE_PATH' '$REMOTE_BACKUP_PATH'
        fi
        mv '$REMOTE_RELEASE_PATH' '$REMOTE_PATH'
    "
    if [ $? -ne 0 ]; then
        echo -e "${RED}Release swap failed. Restoring backup...${NC}"
        ssh_cmd "
            rm -rf '$REMOTE_RELEASE_PATH'
            if [ -d '$REMOTE_BACKUP_PATH' ]; then
                mv '$REMOTE_BACKUP_PATH' '$REMOTE_PATH'
            fi
        "
        exit 1
    fi

    # Restart via PM2
    echo -e "${YELLOW}Restarting application...${NC}"
    ssh_cmd "cd '$REMOTE_PATH' && (pm2 restart $APP_NAME 2>/dev/null || pm2 start ecosystem.config.js --only $APP_NAME)"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Restart failed. Rolling back...${NC}"
        ssh_cmd "
            set -e
            rm -rf '$REMOTE_PATH'
            if [ -d '$REMOTE_BACKUP_PATH' ]; then
                mv '$REMOTE_BACKUP_PATH' '$REMOTE_PATH'
            fi
            cd '$REMOTE_PATH' && (pm2 restart $APP_NAME 2>/dev/null || pm2 start ecosystem.config.js --only $APP_NAME)
        "
        exit 1
    fi

    # Health check
    echo -e "${YELLOW}Running health check...${NC}"
    HEALTH_OK=0
    for i in $(seq 1 10); do
        sleep 2
        HTTP_CODE=$(ssh_cmd "curl -s -o /dev/null -w '%{http_code}' '$APP_HEALTH_URL' 2>/dev/null" || true)
        if [ "$HTTP_CODE" = "200" ]; then
            HEALTH_OK=1
            break
        fi
        echo -e "${YELLOW}  Health check attempt $i: HTTP $HTTP_CODE${NC}"
    done

    if [ "$HEALTH_OK" -ne 1 ]; then
        echo -e "${RED}Health check failed. Rolling back...${NC}"
        ssh_cmd "
            set -e
            rm -rf '$REMOTE_PATH'
            if [ -d '$REMOTE_BACKUP_PATH' ]; then
                mv '$REMOTE_BACKUP_PATH' '$REMOTE_PATH'
            fi
            cd '$REMOTE_PATH' && (pm2 restart $APP_NAME 2>/dev/null || pm2 start ecosystem.config.js --only $APP_NAME)
        "
        exit 1
    fi

    # Verify PM2 status
    PM2_STATUS=$(ssh_cmd "pm2 jlist" 2>/dev/null | grep -o "\"name\":\"$APP_NAME\"[^}]*\"status\":\"[^\"]*\"" | grep -o '"status":"[^"]*"' | head -1 || echo "unknown")
    echo -e "${GREEN}PM2 status: $PM2_STATUS${NC}"

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Deployment Complete!${NC}"
    echo -e "${GREEN}  App: $APP_NAME${NC}"
    echo -e "${GREEN}  URL: https://modelregression.com${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# Run only when executed directly; sourcing (tests) just loads the functions.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
