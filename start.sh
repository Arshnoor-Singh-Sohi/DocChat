#!/bin/bash

# Railway Startup Script for DocChat AI
echo "🚀 Starting DocChat AI on Railway..."

# Use Railway's PORT or default to 8501
PORT=${PORT:-8501}
echo "📍 Using port: $PORT"

# Start Streamlit with proper configuration
exec streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.fileWatcherType=none \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false \
    --theme.base=dark