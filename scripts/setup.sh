#!/bin/sh
# Setup script for Hijaz GeoIntelligence Studio Agent Army
set -e

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "Setting up Hijaz GeoIntelligence Studio..."

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate venv
. venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create data directories
mkdir -p data/channels data/sources data/projects data/reports data/drafts
mkdir -p artifacts logs

# Copy example env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example — please edit with your API keys."
fi

echo ""
echo "Setup complete! Run:"
echo "  source venv/bin/activate"
echo "  python cli/run_pipeline.py --channel geo-daily-ur --topic 'Border update' --dry-run"
echo ""
echo "For Docker:"
echo "  docker-compose up -d"
echo ""
echo "For validation:"
echo "  sh scripts/validate.sh"
