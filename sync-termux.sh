#!/bin/bash
# sync-termux.sh - Bidirectional sync dashboard with Termux
# Supports: Tailscale (remote) + LAN (local) with auto-fallback

USER_TERMUX="u0_a331"
PORT_TERMUX="8022"
TERMUX_PATH="/data/data/com.termux/files/home/dashboard"
PNPM_TERMUX="/data/data/com.termux/files/usr/bin/pnpm"

# IPs (Tailscale = priority, LAN = fallback)
TERMUX_IP_TAILSCALE="${TERMUX_IP:-100.110.26.16}"
TERMUX_IP_LAN="192.168.1.105"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# --- Smart IP Resolver ---
_resolve_termux_ip() {
    # ลอง Tailscale ก่อน (timeout 3s)
    if ssh -o ConnectTimeout=3 -o BatchMode=yes \
           -p "$PORT_TERMUX" \
           "${USER_TERMUX}@${TERMUX_IP_TAILSCALE}" \
           'exit' 2>/dev/null; then
        echo "$TERMUX_IP_TAILSCALE"
        return
    fi
    # Fallback → LAN
    if ssh -o ConnectTimeout=3 -o BatchMode=yes \
           -p "$PORT_TERMUX" \
           "${USER_TERMUX}@${TERMUX_IP_LAN}" \
           'exit' 2>/dev/null; then
        echo "$TERMUX_IP_LAN"
        return
    fi
    echo ""  # ไม่เจอ
}

SSH_OPTS="-p $PORT_TERMUX -o ConnectTimeout=10 -o StrictHostKeyChecking=no"


# Exclude patterns
EXCLUDES="--exclude=node_modules --exclude=.venv --exclude=.env"
EXCLUDES="$EXCLUDES --exclude=.git --exclude=__pycache__ --exclude=*.pyc"
EXCLUDES="$EXCLUDES --exclude=.stfolder --exclude=.stversions --exclude=.stignore"
EXCLUDES="$EXCLUDES --exclude=screenshots --exclude=*.png --exclude=*.jpg"
EXCLUDES="$EXCLUDES --exclude=.chrome_shopee --exclude=openclaw-*"
EXCLUDES="$EXCLUDES --exclude=.ruff_cache --exclude=.pytest_cache"
EXCLUDES="$EXCLUDES --exclude=.pnpm-store --exclude=.pnpm" # pnpm store ไม่ sync ข้ามเครื่อง

# Menu function - source this and run syncterm help
synctm() {
    local cmd="${1:-help}"

    # Auto-resolve IP (skip for help)
    local IP_TERMUX=""
    if [[ "$cmd" != "help" && "$cmd" != "--help" ]]; then
        echo -e "${YELLOW}🔍 Locating Termux...${NC}"
        IP_TERMUX=$(_resolve_termux_ip)
        if [[ -z "$IP_TERMUX" ]]; then
            echo -e "${RED}❌ Cannot reach Termux on Tailscale (${TERMUX_IP_TAILSCALE}) or LAN (${TERMUX_IP_LAN})${NC}"
            echo -e "${YELLOW}   → Check: SSH running? Same WiFi? Tailscale active?${NC}"
            return 1
        fi
        echo -e "${GREEN}✅ Termux found at: ${IP_TERMUX}${NC}"
    fi

    case "$cmd" in
        help|--help)
            echo ""
            echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
            echo -e "${CYAN}║          🚀 Sync Termux Commands                  ║${NC}"
            echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
            echo ""
            echo -e "  ${GREEN}syncterm test${NC}    - ทดสอบการเชื่อมต่อ SSH"
            echo -e "  ${GREEN}syncterm push${NC}    - Push code จาก local ไป Termux"
            echo -e "  ${GREEN}syncterm pull${NC}    - Pull code จาก Termux มา local"
            echo -e "  ${GREEN}syncterm dist${NC}    - Sync frontend/dist (build output)"
            echo -e "  ${GREEN}syncterm both${NC}    - Bidirectional sync (Termux wins)"
            echo -e "  ${GREEN}syncterm deploy${NC}  - Push + pnpm install บน Termux อัตโนมัติ"
            echo -e "  ${GREEN}syncterm ls${NC}      - List files บน Termux"
            echo -e "  ${GREEN}syncterm status${NC}  - ดู sync status"
            echo ""
            echo -e "${YELLOW}  💡 Tips (pnpm workflow):${NC}"
            echo -e "     - Deploy ครั้งแรกหรือเปลี่ยน deps: ${CYAN}syncterm deploy${NC}"
            echo -e "     - แก้ code อย่างเดียว: ${CYAN}syncterm push${NC}"
            echo -e "     - หลัง build: ${CYAN}syncterm dist${NC} เพื่อ sync dist ไป Termux"
            echo -e "     - ก่อนแก้ code: ${CYAN}syncterm pull${NC} เพื่อดึงล่าสุดมาก่อน"
            echo ""
            ;;
        test)
            echo -e "${CYAN}🔍 Testing connection...${NC}"
            ssh $SSH_OPTS "${USER_TERMUX}@${IP_TERMUX}" "echo '✅ SSH OK' && ls -la ~/dashboard 2>/dev/null | head -3 || echo '❌ Dashboard folder not found'"
            ;;
        push)
            echo -e "${CYAN}📤 Pushing to Termux...${NC}"
            rsync -avz $EXCLUDES -e "ssh $SSH_OPTS" ~/dashboard/ "${USER_TERMUX}@${IP_TERMUX}:${TERMUX_PATH}/"
            echo -e "${GREEN}✅ Push complete!${NC}"
            echo -e "${YELLOW}  💡 Tip: ถ้าเปลี่ยน dependencies ให้รัน: ${CYAN}syncterm deploy${NC}${NC}"
            ;;
        pull)
            echo -e "${CYAN}📥 Pulling from Termux...${NC}"
            rsync -avz $EXCLUDES -e "ssh $SSH_OPTS" "${USER_TERMUX}@${IP_TERMUX}:${TERMUX_PATH}/" ~/dashboard/
            echo -e "${GREEN}✅ Pull complete!${NC}"
            ;;
        dist)
            echo -e "${CYAN}📦 Syncing frontend/dist to Termux...${NC}"
            rsync -avz --exclude=node_modules -e "ssh $SSH_OPTS" ~/dashboard/frontend/dist/ "${USER_TERMUX}@${IP_TERMUX}:${TERMUX_PATH}/frontend/dist/"
            echo -e "${GREEN}✅ Dist sync complete!${NC}"
            ;;
        both)
            echo -e "${CYAN}🔄 Bidirectional sync...${NC}"
            echo -e "${YELLOW}  Step 1: Pull from Termux${NC}"
            rsync -avz $EXCLUDES -e "ssh $SSH_OPTS" "${USER_TERMUX}@${IP_TERMUX}:${TERMUX_PATH}/" ~/dashboard/
            echo -e "${YELLOW}  Step 2: Push to Termux${NC}"
            rsync -avz $EXCLUDES -e "ssh $SSH_OPTS" ~/dashboard/ "${USER_TERMUX}@${IP_TERMUX}:${TERMUX_PATH}/"
            echo -e "${GREEN}✅ Bidirectional sync complete!${NC}"
            ;;
        deploy)
            echo -e "${CYAN}🚀 Deploy: Push + pnpm install on Termux...${NC}"
            echo -e "${YELLOW}  Step 1: Push code to Termux${NC}"
            rsync -avz $EXCLUDES -e "ssh $SSH_OPTS" ~/dashboard/ "${USER_TERMUX}@${IP_TERMUX}:${TERMUX_PATH}/"
            echo -e "${YELLOW}  Step 2: Run pnpm install on Termux (frontend)${NC}"
            ssh $SSH_OPTS "${USER_TERMUX}@${IP_TERMUX}" \
                "cd ${TERMUX_PATH}/frontend && ${PNPM_TERMUX} install --reporter=silent && echo '✅ pnpm install done' || echo '❌ pnpm install failed'"
            echo -e "${GREEN}✅ Deploy complete!${NC}"
            ;;
        ls)
            echo -e "${CYAN}📂 Files on Termux:${NC}"
            ssh $SSH_OPTS "${USER_TERMUX}@${IP_TERMUX}" "ls -la ${TERMUX_PATH}/ 2>/dev/null | head -20 || echo '❌ Cannot list'"
            ;;
        status)
            echo -e "${CYAN}📊 Sync Status:${NC}"
            echo -e "  Local:  ~/dashboard"
            echo -e "  Remote: ${USER_TERMUX}@${IP_TERMUX}:${TERMUX_PATH}"
            echo ""
            echo -e "${YELLOW}Checking Termux...${NC}"
            ssh $SSH_OPTS "${USER_TERMUX}@${IP_TERMUX}" "echo '✅ Termux online' && df -h ~/dashboard 2>/dev/null | tail -1 || echo '⚠️ Cannot check space'"
            ;;
        *)
            echo -e "${RED}Unknown command: $cmd${NC}"
            echo -e "พิมพ์ ${GREEN}syncterm${NC} เพื่อดู help"
            ;;
    esac
}

# If run directly (not sourced), show help
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    synctm "$@"
fi
