#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Configurable variable for the expected directory
EXPECTED_DIR="/opt/edge-privacy-switch"

# Step 0: Validate the current directory
if [ "$PWD" != "$EXPECTED_DIR" ]; then
    echo "Error: Script must be run from $EXPECTED_DIR, but current directory is $PWD."
    exit 1
fi

echo "Starting setup in $PWD..."

# Step 1: Update package lists
echo "Updating package lists..."
sudo apt update

# Step 2: Install Python and necessary packages
echo "Installing Python and necessary dependencies..."
sudo apt install -y python3-venv python3-pip python-is-python3

# Step 3: Create Python virtual environment if not already created
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Step 4: Install Python packages from requirements.txt
if [ -f "edge-privacy-switch/requirements.txt" ]; then
    echo "Installing Python packages from requirements.txt..."
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r edge-privacy-switch/requirements.txt
    echo "Packages installed successfully!"
else
    echo "edge-privacy-switch/requirements.txt not found! Skipping package installation."
fi

# Step 5: Set up systemd service
SERVICE_FILE="edge-privacy-switch-agent.service"

if [ -f "$SERVICE_FILE" ]; then
    echo "Copying systemd service file..."
    sudo cp $SERVICE_FILE /etc/systemd/system/

    echo "Reloading systemd daemon and configuring the service..."
    sudo systemctl daemon-reload
    sudo systemctl enable edge-privacy-switch-agent.service

    echo "Starting the service..."
    sudo systemctl start edge-privacy-switch-agent.service

    # Show service status
    sudo systemctl status edge-privacy-switch-agent.service --no-pager
    echo "Service successfully configured and started!"
else
    echo "$SERVICE_FILE not found! Skipping service setup."
fi

echo "Setup complete!"