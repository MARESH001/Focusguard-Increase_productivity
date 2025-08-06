#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install system dependencies
apt-get update && apt-get install -y build-essential gcc g++ python3-dev

# Update pip and install build tools
pip install --upgrade pip setuptools wheel

# Set environment variables for compilation optimization
export BLIS_ARCH="x86_64"
export NPY_NUM_BUILD_JOBS=1
export MAKEFLAGS="-j1"

# Install packages with no cache and prefer binary wheels
pip install --no-cache-dir --prefer-binary -r requirements.txt

# Verify spaCy installation
python -c "import spacy; print('spaCy installed successfully')"

# Verify spaCy model
python -c "import en_core_web_sm; print('spaCy model loaded successfully')"
