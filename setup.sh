#!/bin/bash
# ============================================
# DomiSafe IoT System - Setup Script
# ============================================
# This script automates the installation and setup process
# Run with: chmod +x setup.sh && ./setup.sh

set -e  # Exit on any error

echo "=================================================="
echo "🏠 DomiSafe IoT System Setup"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Raspberry Pi
echo -e "${YELLOW}📋 Checking system...${NC}"
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo -e "${GREEN}✅ Detected: $MODEL${NC}"
else
    echo -e "${YELLOW}⚠️  Not detected as Raspberry Pi, continuing anyway...${NC}"
fi
echo ""

# Update system packages
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt-get update -qq
echo -e "${GREEN}✅ System updated${NC}"
echo ""

# Install required system packages
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    libgpiod2 \
    libatlas-base-dev \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff5 \
    libpq-dev \
    build-essential \
    -qq

echo -e "${GREEN}✅ System packages installed${NC}"
echo ""

# Create virtual environment
echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists, removing...${NC}"
    rm -rf venv
fi

python3 -m venv venv
echo -e "${GREEN}✅ Virtual environment created${NC}"
echo ""

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${YELLOW}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip -q
echo -e "${GREEN}✅ pip upgraded${NC}"
echo ""

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python packages...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    echo -e "${GREEN}✅ Python packages installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found!${NC}"
    exit 1
fi
echo ""

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p captures
mkdir -p backups
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Initialize local database
echo -e "${YELLOW}💾 Initializing local database...${NC}"
python3 << EOF
from modules.local_db import init_db
try:
    init_db()
    print("✅ Database initialized")
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    exit(1)
EOF
echo ""

# Check for config file
echo -e "${YELLOW}⚙️  Checking configuration...${NC}"
if [ ! -f "config.json" ]; then
    if [ -f "config.example.json" ]; then
        echo -e "${YELLOW}⚠️  config.json not found, copying from example...${NC}"
        cp config.example.json config.json
        echo -e "${YELLOW}⚠️  IMPORTANT: Edit config.json with your credentials!${NC}"
        echo -e "${YELLOW}   - Adafruit IO username and key${NC}"
        echo -e "${YELLOW}   - Neon database URL${NC}"
        echo -e "${YELLOW}   - GPIO pin numbers${NC}"
    else
        echo -e "${RED}❌ No config.example.json found!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ config.json exists${NC}"
fi
echo ""

# Enable camera (if on Raspberry Pi)
echo -e "${YELLOW}📸 Checking camera configuration...${NC}"
if command -v raspi-config &> /dev/null; then
    echo -e "${YELLOW}⚠️  Please enable camera manually:${NC}"
    echo -e "${YELLOW}   sudo raspi-config${NC}"
    echo -e "${YELLOW}   Interface Options → Camera → Enable${NC}"
else
    echo -e "${YELLOW}⚠️  raspi-config not found, skipping camera setup${NC}"
fi
echo ""

# Set permissions for GPIO
echo -e "${YELLOW}🔐 Setting GPIO permissions...${NC}"
if groups | grep -q gpio; then
    echo -e "${GREEN}✅ User already in gpio group${NC}"
else
    echo -e "${YELLOW}⚠️  Adding user to gpio group...${NC}"
    sudo usermod -a -G gpio $USER
    echo -e "${YELLOW}⚠️  You may need to logout/login for changes to take effect${NC}"
fi
echo ""

# Create systemd service file (optional)
echo -e "${YELLOW}🔧 Creating systemd service file...${NC}"
SERVICE_FILE="/tmp/domisafe.service"
cat > $SERVICE_FILE << EOSERVICE
[Unit]
Description=DomiSafe IoT Home Security System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 $(pwd)/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOSERVICE

echo -e "${GREEN}✅ Service file created at $SERVICE_FILE${NC}"
echo -e "${YELLOW}   To install service:${NC}"
echo -e "${YELLOW}   sudo cp $SERVICE_FILE /etc/systemd/system/${NC}"
echo -e "${YELLOW}   sudo systemctl daemon-reload${NC}"
echo -e "${YELLOW}   sudo systemctl enable domisafe${NC}"
echo -e "${YELLOW}   sudo systemctl start domisafe${NC}"
echo ""

# Final summary
echo "=================================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=================================================="
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo "1. Edit configuration:"
echo "   nano config.json"
echo ""
echo "2. Test the system:"
echo "   source venv/bin/activate"
echo "   python3 test_system.py"
echo ""
echo "3. Run main application:"
echo "   python3 main.py"
echo ""
echo "4. Run Flask web app (in another terminal):"
echo "   source venv/bin/activate"
echo "   cd web_app"
echo "   python3 app.py"
echo ""
echo "5. Access dashboard:"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo -e "${GREEN}Happy IoT building! 🚀${NC}"
echo ""