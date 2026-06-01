#!/bin/bash
set -e

# ANSI color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "==============================="
echo "  Calcify - Debian Setup"
echo "==============================="

# 1. Python3 Check
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 is not installed.${NC}"
    echo -e "${RED}Run 'sudo apt install python3' to install it.${NC}"
    exit 1
fi

# 2. Venv Package Check
if ! dpkg -l | grep -q python3-venv; then
    echo -e "${YELLOW}Warning: python3-venv not found. Attempting to install...${NC}"
    sudo apt update && sudo apt install -y python3-venv python3-pip || {
        echo -e "${RED}Failed to install python3-venv. Please run with sudo or install manually.${NC}"
        exit 1
    }
fi

# 3. Workspace setup
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 4. Activate and update
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. DB & Security Init
alembic upgrade head
python3 setup_security.py

# 6. LAN IP resolution
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP=$(ip route get 1.1.1.1 | awk '{print $7}')
fi

# 7. Banner
echo ""
echo "============================================"
echo "  Calcify is now available at:"
echo ""
echo "  Local:    http://localhost:5000"
echo "  Network:  http://${LOCAL_IP}:5000"
echo ""
echo "  Press Ctrl+C to stop the server"
echo "============================================"
echo ""

# 8. Execution
python3 app.py
