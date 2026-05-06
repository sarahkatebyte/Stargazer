#!/bin/bash
# Build script for production deployment
# Railway/Render runs this before starting the server

set -e

echo "==> Building React frontend..."
cd frontend
rm -rf node_modules package-lock.json
npm install --include=optional
npm run build
cd ..

echo "==> Collecting static files..."
python3 manage.py collectstatic --noinput

echo "==> Running migrations..."
python3 manage.py migrate --noinput

echo "==> Build complete!"
