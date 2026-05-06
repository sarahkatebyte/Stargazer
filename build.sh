#!/bin/bash
# Build script for production deployment
# Railway/Render runs this before starting the server

set -e

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Building React frontend..."
cd frontend
rm -rf node_modules package-lock.json
npm install --include=optional
npm run build
cd ..

echo "==> Build complete!"
