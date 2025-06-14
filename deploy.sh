#!/bin/bash

# DocChat AI Deployment Script
echo "🚀 DocChat AI Deployment Script"
echo "================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Creating from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys!"
    exit 1
fi

# Check if API key is set
if grep -q "your-actual-key-here" .env; then
    echo "❌ Please update your API keys in .env file!"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p .streamlit
mkdir -p backend

# Check if all files exist
echo "🔍 Checking files..."
files=(".streamlit/config.toml" "backend/__init__.py" "backend/rag.py" "backend/scraper.py" "app.py" "requirements.txt" "railway.json" "nixpacks.toml")

for file in "${files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        missing=true
    else
        echo "✅ Found: $file"
    fi
done

if [ "$missing" = true ]; then
    echo "❌ Some files are missing. Please create them first."
    exit 1
fi

# Install Railway CLI if not installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "🔐 Logging into Railway..."
railway login

# Initialize or link project
echo "🚂 Setting up Railway project..."
railway link || railway init

# Set environment variables
echo "🔧 Setting environment variables..."
source .env
railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
railway variables set QDRANT_URL="$QDRANT_URL"
railway variables set QDRANT_API_KEY="$QDRANT_API_KEY"

# Deploy
echo "🚀 Deploying to Railway..."
railway up

# Get deployment URL
echo "✅ Deployment complete!"
echo "🌐 Opening your app..."
railway open

echo ""
echo "🎉 DocChat AI is now live!"
echo "================================"
echo "Next steps:"
echo "1. Wait for the build to complete (3-5 minutes)"
echo "2. Visit your app URL"
echo "3. Start chatting with documentation!"