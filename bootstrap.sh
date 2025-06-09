#!/bin/bash

set -e

echo "🛠️  Setting up DevPilot..."

# Step 1: Create virtualenv if not exists
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created."
fi

# Step 2: Activate virtualenv
source .venv/bin/activate

# Step 3: Upgrade pip + install DevPilot
pip install --upgrade pip
pip install --editable .

echo ""
echo "🎉 DevPilot installed successfully!"
echo "👉 Run like this:"
echo "   devpilot path/to/file.py --mode=onboard"
echo "   devpilot path/to/file.py --mode=explain"
echo "   devpilot path/to/file.py --mode=refactor"
echo ""

