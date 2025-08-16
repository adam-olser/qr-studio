#!/bin/bash

# QR Studio - Deployment Setup Script
# This script helps prepare your repository for free deployment

set -e

echo "🚀 QR Studio Deployment Setup"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "package.json" ] && [ ! -f "backend/requirements.txt" ]; then
    print_error "Please run this script from the QR Studio root directory"
    exit 1
fi

print_info "Checking deployment readiness..."

# Check if GitHub Actions workflow exists
if [ -f ".github/workflows/ci-cd.yml" ]; then
    print_status "GitHub Actions workflow found"
else
    print_error "GitHub Actions workflow not found"
    echo "Please ensure .github/workflows/ci-cd.yml exists"
    exit 1
fi

# Check if deployment configs exist
if [ -f "railway.json" ]; then
    print_status "Railway configuration found"
else
    print_warning "Railway configuration not found (optional)"
fi

if [ -f "render.yaml" ]; then
    print_status "Render configuration found"
else
    print_warning "Render configuration not found (optional)"
fi

# Run tests to ensure everything works
print_info "Running tests..."

# Backend tests
if [ -d "backend" ]; then
    print_info "Testing backend..."
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
    else
        if [ -d "venv" ]; then
            source venv/bin/activate
        elif [ -d ".venv" ]; then
            source .venv/bin/activate
        fi
    fi
    
    # Install dependencies
    print_info "Installing backend dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Run type checking
    if [ -f "scripts/type-check.sh" ]; then
        print_info "Running type checking..."
        chmod +x scripts/type-check.sh
        ./scripts/type-check.sh
        print_status "Backend type checking passed"
    fi
    
    # Run tests
    if [ -f "scripts/run-tests.sh" ]; then
        print_info "Running backend tests..."
        chmod +x scripts/run-tests.sh
        REDIS_URL="redis://localhost:6379" ENV="testing" ./scripts/run-tests.sh
        print_status "Backend tests passed"
    fi
    
    cd ..
fi

# Frontend tests
if [ -d "frontend" ]; then
    print_info "Testing frontend..."
    cd frontend
    
    # Install dependencies
    print_info "Installing frontend dependencies..."
    npm ci > /dev/null 2>&1
    
    # Run type checking
    print_info "Running frontend type checking..."
    npm run type-check
    print_status "Frontend type checking passed"
    
    # Run tests
    print_info "Running frontend tests..."
    npm test -- --run
    print_status "Frontend tests passed"
    
    # Test build
    print_info "Testing production build..."
    npm run build > /dev/null 2>&1
    print_status "Frontend build successful"
    
    cd ..
fi

echo ""
print_status "All checks passed! Your app is ready for deployment."
echo ""

print_info "Next steps:"
echo "1. Push your code to GitHub:"
echo "   git add ."
echo "   git commit -m 'Prepare for deployment'"
echo "   git push origin main"
echo ""
echo "2. Set up backend deployment:"
echo "   - Railway.app: https://railway.app (recommended)"
echo "   - Render.com: https://render.com (alternative)"
echo ""
echo "3. Configure GitHub Pages:"
echo "   - Go to your repo → Settings → Pages"
echo "   - Source: GitHub Actions"
echo ""
echo "4. Update environment variables:"
echo "   - Add VITE_API_URL to GitHub Secrets"
echo "   - Update CORS_ORIGINS in backend deployment"
echo ""
echo "📚 See DEPLOYMENT.md for detailed instructions"
echo ""
print_status "Happy deploying! 🎉"
