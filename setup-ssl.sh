#!/bin/bash
# ============================================
# SSL Certificate Setup for ModelRegression.com
# Deploys certs to Linode server and configures Nginx
# ============================================

set -euo pipefail

if [ -f ".deploy.env" ]; then
    source .deploy.env
fi

SERVER_IP="${DEPLOY_SERVER_IP:-}"
SERVER_PORT="${DEPLOY_SERVER_PORT:-44444}"
SERVER_USER="${DEPLOY_SERVER_USER:-root}"
SERVER_PASS="${DEPLOY_SERVER_PASS:-}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$SERVER_IP" ]; then
    echo -e "${RED}Error: Missing DEPLOY_SERVER_IP in .deploy.env${NC}"
    exit 1
fi

SSH_OPTS="-p $SERVER_PORT -o StrictHostKeyChecking=no"
if [ -n "$SERVER_PASS" ]; then
    if ! command -v sshpass >/dev/null 2>&1; then
        echo -e "${RED}sshpass is required for password auth.${NC}"
        exit 1
    fi
    ssh_cmd() {
        sshpass -p "$SERVER_PASS" ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$1"
    }
    scp_cmd() {
        sshpass -p "$SERVER_PASS" scp -P "$SERVER_PORT" -o StrictHostKeyChecking=no "$@"
    }
else
    ssh_cmd() {
        ssh $SSH_OPTS "$SERVER_USER@$SERVER_IP" "$1"
    }
    scp_cmd() {
        scp -P "$SERVER_PORT" -o StrictHostKeyChecking=no "$@"
    }
fi

WORK_DIR="/tmp/ssl_extract"
SSL_REMOTE_DIR="/etc/ssl/modelregression.com"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SSL Setup for ModelRegression.com${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Extract certs locally
echo -e "${YELLOW}Extracting certificates...${NC}"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"
unzip -o ssl.zip -d "$WORK_DIR" > /dev/null
unzip -o "$WORK_DIR/modelregression.com-certificates.zip" -d "$WORK_DIR" > /dev/null

# Create fullchain (cert + intermediate + cross-signed)
cat "$WORK_DIR/modelregression.com-certificate.pem" \
    "$WORK_DIR/modelregression.com-intermediate.pem" \
    "$WORK_DIR/modelregression.com-cross.pem" \
    > "$WORK_DIR/fullchain.pem"

echo -e "${GREEN}Certificates extracted${NC}"

# Step 2: Create remote SSL directory and upload
echo -e "${YELLOW}Uploading certificates to server...${NC}"
ssh_cmd "mkdir -p $SSL_REMOTE_DIR && chmod 700 $SSL_REMOTE_DIR"

scp_cmd "$WORK_DIR/fullchain.pem" "$SERVER_USER@$SERVER_IP:$SSL_REMOTE_DIR/fullchain.pem"
scp_cmd "$WORK_DIR/modelregression.com-PrivateKey.pem" "$SERVER_USER@$SERVER_IP:$SSL_REMOTE_DIR/privkey.pem"

ssh_cmd "chmod 644 $SSL_REMOTE_DIR/fullchain.pem && chmod 600 $SSL_REMOTE_DIR/privkey.pem"
echo -e "${GREEN}Certificates uploaded${NC}"

# Step 3: Deploy Nginx config
echo -e "${YELLOW}Deploying Nginx configuration...${NC}"
scp_cmd "config/nginx-modelregression.conf" "$SERVER_USER@$SERVER_IP:/etc/nginx/sites-available/modelregression.conf"

ssh_cmd "
    ln -sf /etc/nginx/sites-available/modelregression.conf /etc/nginx/sites-enabled/modelregression.conf
    nginx -t
"
if [ $? -ne 0 ]; then
    echo -e "${RED}Nginx config test failed!${NC}"
    exit 1
fi
echo -e "${GREEN}Nginx config valid${NC}"

# Step 4: Reload Nginx
echo -e "${YELLOW}Reloading Nginx...${NC}"
ssh_cmd "systemctl reload nginx"
echo -e "${GREEN}Nginx reloaded${NC}"

# Step 5: Verify SSL
echo -e "${YELLOW}Verifying SSL...${NC}"
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "https://modelregression.com" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}SSL is working! (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${YELLOW}Could not verify SSL externally (HTTP $HTTP_CODE).${NC}"
    echo -e "${YELLOW}This may be normal if DNS hasn't propagated yet.${NC}"
fi

# Cleanup
rm -rf "$WORK_DIR"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SSL Setup Complete!${NC}"
echo -e "${GREEN}  Certs: $SSL_REMOTE_DIR${NC}"
echo -e "${GREEN}  Nginx: /etc/nginx/sites-available/modelregression.conf${NC}"
echo -e "${GREEN}========================================${NC}"
