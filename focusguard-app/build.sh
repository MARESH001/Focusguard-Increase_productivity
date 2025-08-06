#!/usr/bin/env bash
# exit on error
set -o errexit

# Update pip and install build tools
pip install --upgrade pip setuptools wheel

# Install packages with no cache to avoid compilation issues
pip install --no-cache-dir -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
