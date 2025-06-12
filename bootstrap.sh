#!/bin/bash

set -e

echo "\n🛠️  Setting up DevPilot..."

# Create virtual environment
python3 -m venv .venv
echo "✅ Virtual environment created."

# Activate it
source .venv/bin/activate

# Upgrade pip & install in editable mode
pip install --upgrade pip
pip install --editable .

# Install required Python packages
echo "📦 Installing required Python packages (requests, rich)..."
pip install requests rich


# Add global symlink if not already present
if [ ! -f /usr/local/bin/devpilot ]; then
    echo "🔗 Creating global devpilot command..."
    sudo ln -sf "$PWD/.venv/bin/devpilot" /usr/local/bin/devpilot
    echo "✅ Global command created. Run 'devpilot --help' to verify."
else
    echo "ℹ️  Global command already exists at /usr/local/bin/devpilot"
fi

echo "🎉 Setup complete. You can now use: devpilot /path/to/code --mode=onboard"

