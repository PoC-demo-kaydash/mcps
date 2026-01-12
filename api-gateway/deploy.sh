#!/bin/bash

# API Gateway Deployment Script

set -e

echo "================================"
echo "API Gateway Deployment"
echo "================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/app/poc/mcps/api-gateway"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="mcp-api-gateway"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in correct directory
if [ ! -f "$APP_DIR/main.py" ]; then
    log_error "main.py not found. Please run from api-gateway directory."
    exit 1
fi

cd "$APP_DIR"

# Step 1: Check Python version
log_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log_info "Python version: $PYTHON_VERSION"

# Step 2: Create virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    log_info "Virtual environment already exists"
fi

# Step 3: Activate virtual environment
log_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Step 4: Install dependencies
log_info "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Check .env file
if [ ! -f "$APP_DIR/.env" ]; then
    log_warn ".env file not found"
    log_info "Creating .env from .env.example..."
    cp .env.example .env
    log_warn "Please update .env file with your configuration"
    log_warn "Especially: JWT_SECRET_KEY, DB_PASSWORD, REDIS_PASSWORD"
    read -p "Press enter to continue after updating .env..."
fi

# Step 6: Run tests (optional)
if [ -d "$APP_DIR/tests" ]; then
    log_info "Running tests..."
    pytest tests/ -v || log_warn "Some tests failed, continuing anyway..."
fi

# Step 7: Check if systemd service exists
if systemctl list-units --full -all | grep -Fq "$SERVICE_NAME.service"; then
    log_info "Restarting systemd service: $SERVICE_NAME"
    sudo systemctl restart "$SERVICE_NAME"
    sudo systemctl status "$SERVICE_NAME" --no-pager
else
    log_warn "Systemd service not found: $SERVICE_NAME"
    log_info "Starting application manually..."
    
    # Kill existing process
    pkill -f "uvicorn main:app" || true
    
    # Start in background
    nohup python3 main.py > /tmp/api-gateway.log 2>&1 &
    API_PID=$!
    log_info "Started API Gateway with PID: $API_PID"
fi

# Step 8: Wait for service to start
log_info "Waiting for service to start..."
sleep 5

# Step 9: Health check
log_info "Performing health check..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log_info "Health check passed!"
        curl -s http://localhost:8080/health | python3 -m json.tool
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_warn "Health check failed, retrying ($RETRY_COUNT/$MAX_RETRIES)..."
        sleep 2
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Health check failed after $MAX_RETRIES attempts"
    exit 1
fi

# Step 10: Display service info
echo ""
echo "================================"
log_info "Deployment completed successfully!"
echo "================================"
echo ""
echo "Service Information:"
echo "  - API Gateway URL: http://localhost:8080"
echo "  - Health Check: http://localhost:8080/health"
echo "  - API Docs: http://localhost:8080/docs (if not production)"
echo "  - ReDoc: http://localhost:8080/redoc (if not production)"
echo ""
log_info "To view logs: tail -f /tmp/api-gateway.log"
log_info "To stop: pkill -f 'uvicorn main:app'"
echo ""
