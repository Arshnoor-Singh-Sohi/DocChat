# DocChat AI Deployment Script for Windows
Write-Host "🚀 DocChat AI Deployment Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if .env exists
if (!(Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please edit .env and add your API keys!" -ForegroundColor Yellow
    exit 1
}

# Check if API key is set
$envContent = Get-Content ".env"
if ($envContent -match "your-actual-key-here") {
    Write-Host "❌ Please update your API keys in .env file!" -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path ".streamlit" | Out-Null
New-Item -ItemType Directory -Force -Path "backend" | Out-Null

# Check if all files exist
Write-Host "🔍 Checking files..." -ForegroundColor Green
$files = @(
    ".streamlit/config.toml",
    "backend/__init__.py",
    "backend/rag.py",
    "backend/scraper.py",
    "app.py",
    "requirements.txt",
    "railway.json",
    "nixpacks.toml"
)

$missing = $false
foreach ($file in $files) {
    if (!(Test-Path $file)) {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
        $missing = $true
    } else {
        Write-Host "✅ Found: $file" -ForegroundColor Green
    }
}

if ($missing) {
    Write-Host "❌ Some files are missing. Please create them first." -ForegroundColor Red
    exit 1
}

# Check if Railway CLI is installed
try {
    railway --version | Out-Null
} catch {
    Write-Host "📦 Installing Railway CLI..." -ForegroundColor Yellow
    npm install -g @railway/cli
}

# Login to Railway
Write-Host "🔐 Logging into Railway..." -ForegroundColor Green
railway login

# Initialize or link project
Write-Host "🚂 Setting up Railway project..." -ForegroundColor Green
try {
    railway link
} catch {
    railway init
}

# Read environment variables
Write-Host "🔧 Setting environment variables..." -ForegroundColor Green
$envVars = @{}
Get-Content ".env" | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.+)$") {
        $envVars[$matches[1].Trim()] = $matches[2].Trim()
    }
}

# Set Railway variables
railway variables set OPENAI_API_KEY=$($envVars["OPENAI_API_KEY"])
railway variables set QDRANT_URL=$($envVars["QDRANT_URL"])
if ($envVars.ContainsKey("QDRANT_API_KEY")) {
    railway variables set QDRANT_API_KEY=$($envVars["QDRANT_API_KEY"])
}

# Deploy
Write-Host "🚀 Deploying to Railway..." -ForegroundColor Cyan
railway up

# Get deployment URL
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌐 Opening your app..." -ForegroundColor Green
railway open

Write-Host ""
Write-Host "🎉 DocChat AI is now live!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Wait for the build to complete (3-5 minutes)"
Write-Host "2. Visit your app URL"
Write-Host "3. Start chatting with documentation!"