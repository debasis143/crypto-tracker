#!/bin/bash

# Ensure pip is available
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip

# Install virtualenv
pip install virtualenv

# Create virtual environment (optional, but recommended)
virtualenv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "✅ All packages installed."
