#!/bin/bash

# Calorie Track AI Bot - Development Setup Script
# This script helps set up the development environment

set -e

echo "Calorie Track AI Bot - Development Setup"
echo ""

# Check if we're in the right directory
if [ ! -f "Makefile" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "Please run this script from the project root directory"
    exit 1
fi

echo "Setting up development environment..."
echo ""

# Step 1: Check dependencies
echo "Step 1: Checking dependencies..."
make check-deps

# Step 2: Install dependencies
echo ""
echo "Step 2: Installing dependencies..."
make setup

# Step 3: Create environment files if they don't exist
echo ""
echo "Step 3: Setting up environment files..."

# Backend .env
if [ ! -f "backend/.env" ]; then
    echo "Creating backend/.env template..."
    cat > backend/.env << 'EOF'
# Application
APP_ENV=dev

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-5-mini

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Redis
REDIS_URL=redis://localhost:6379

# Tigris/S3
AWS_ENDPOINT_URL_S3=https://fly.storage.tigris.dev
AWS_ACCESS_KEY_ID=tid_xxxxxx
AWS_SECRET_ACCESS_KEY=tsec_xxxxxx
BUCKET_NAME=your-bucket-name

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Logging
LOG_LEVEL=INFO
EOF
    echo "Please edit backend/.env with your actual service credentials"
else
    echo "backend/.env already exists"
fi

# Frontend .env.local
if [ ! -f "frontend/.env.local" ]; then
    echo "Creating frontend/.env.local..."
    cat > frontend/.env.local << 'EOF'
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Development Features
VITE_ENABLE_DEBUG_LOGGING=true
VITE_ENABLE_ERROR_REPORTING=false
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEV_TOOLS=true

# App Metadata
VITE_APP_VERSION=1.0.0

# API Timeout (milliseconds)
VITE_API_TIMEOUT=30000
EOF
    echo "frontend/.env.local created"
else
    echo "frontend/.env.local already exists"
fi

# Step 4: Final instructions
echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your service credentials"
echo "2. Run 'make dev' to start development servers"
echo "3. Visit http://localhost:8000/docs for API documentation"
echo "4. Visit http://localhost:5173 for the frontend application"
echo ""
echo "Useful commands:"
echo "  make dev          - Start both backend and frontend"
echo "  make test         - Run all tests"
echo "  make help         - Show all available commands"
echo "  make health-check - Check if backend is running"
echo ""
echo "For more information, see DEVELOPMENT.md"
