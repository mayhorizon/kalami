#!/bin/bash
# Kalami Gateway Setup Script

set -e

echo "======================================"
echo "Kalami Gateway Setup"
echo "======================================"
echo ""

# Check Node.js version
echo "Checking Node.js version..."
NODE_VERSION=$(node --version)
echo "Node.js version: $NODE_VERSION"

REQUIRED_MAJOR=18
CURRENT_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')

if [ "$CURRENT_MAJOR" -lt "$REQUIRED_MAJOR" ]; then
  echo "ERROR: Node.js >= 18.0.0 is required"
  exit 1
fi

echo "✓ Node.js version OK"
echo ""

# Install dependencies
echo "Installing npm dependencies..."
npm install
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
  echo "Creating .env file from .env.example..."
  cp .env.example .env
  echo "✓ .env file created"
  echo ""
  echo "⚠️  IMPORTANT: Edit .env and set a secure JWT_SECRET before running in production!"
  echo ""
else
  echo ".env file already exists"
  echo ""
fi

# Build TypeScript
echo "Building TypeScript..."
npm run build
echo "✓ Build completed"
echo ""

echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and configure environment variables"
echo "2. Ensure FastAPI backend is running at BACKEND_URL"
echo "3. Run tests: npm test"
echo "4. Start development server: npm run dev"
echo "5. Or start production server: npm start"
echo ""
