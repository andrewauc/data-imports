#!/bin/bash
# Setup script for Meltano ETL project

set -e

echo "==================================="
echo "Meltano ETL Project Setup"
echo "==================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Found Python $PYTHON_VERSION"

# Check if Docker is installed (optional)
if command -v docker &> /dev/null; then
    echo "✓ Found Docker $(docker --version | cut -d ' ' -f3)"
else
    echo "⚠ Docker not found. Docker is optional but recommended for containerized deployment."
fi

echo ""
echo "Step 1: Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"

echo ""
echo "Step 2: Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

echo ""
echo "Step 3: Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Python dependencies installed"

echo ""
echo "Step 4: Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo "⚠ Please edit .env file with your InfluxDB credentials"
else
    echo "⚠ .env file already exists, skipping"
fi

echo ""
echo "Step 5: Creating Meltano directories..."
mkdir -p .meltano
echo "✓ Meltano directory created"

echo ""
echo "Step 6: Updating .env with project root..."
PROJECT_ROOT=$(pwd)
if grep -q "MELTANO_PROJECT_ROOT=" .env 2>/dev/null; then
    # If already exists, update it
    sed -i.bak "s|MELTANO_PROJECT_ROOT=.*|MELTANO_PROJECT_ROOT=$PROJECT_ROOT|g" .env && rm .env.bak
else
    # If not exists, add it
    echo "MELTANO_PROJECT_ROOT=$PROJECT_ROOT" >> .env
fi
# Also update the DATABASE_URI to use absolute path
sed -i.bak "s|MELTANO_DATABASE_URI=.*|MELTANO_DATABASE_URI=sqlite:///$PROJECT_ROOT/.meltano/meltano.db|g" .env && rm .env.bak
echo "✓ Updated .env with project paths"

echo ""
echo "Step 7: Installing Meltano plugins..."
meltano install
echo "✓ Meltano plugins installed"

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your InfluxDB credentials:"
echo "   nano .env"
echo ""
echo "2. Activate the virtual environment (if not already active):"
echo "   source venv/bin/activate"
echo ""
echo "3. Test the pipeline:"
echo "   meltano run nationalgas-to-influxdb"
echo ""
echo "4. For Docker deployment:"
echo "   docker-compose up -d"
echo ""
echo "For more information, see README.md"
