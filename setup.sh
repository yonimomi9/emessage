#!/bin/bash

echo "Starting setup..."

# Update packages
sudo apt update

# Install Python3 and pip
sudo apt install -y python3 python3-pip

# Install required Python packages
echo "Installing Python dependencies..."
pip install --upgrade pip
pip3 install pillow

# Make sure test.py can find modules
export PYTHONPATH=$(pwd)

# Run automated tests
echo "Running tests..."
python3 tests.py

echo "✅ Setup complete!"