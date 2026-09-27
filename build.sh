#!/usr/bin/env bash
# =============================================================================
# AeroNex Unified Build Script for Full-Stack Render Deployment
# =============================================================================
set -o errexit

echo ">>> [1/3] Building AeroNex React Frontend..."
cd frontend
npm install
npm run build
cd ..

echo ">>> [2/3] Installing AeroNex Python Backend Dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo ">>> [3/3] AeroNex Build Completed Successfully!"
