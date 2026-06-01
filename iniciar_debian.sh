#!/bin/bash

# BSD 3-Clause License
#
# Copyright (c) 2026, yorlysoro
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
