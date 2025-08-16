#!/bin/bash

# QR Studio Production Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"
LOG_FILE="./deploy.log"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        warn "Environment file $ENV_FILE not found"
        if [ -f "env.example" ]; then
            info "Copying env.example to $ENV_FILE"
            cp env.example "$ENV_FILE"
            warn "Please edit $ENV_FILE with your production values before continuing"
            exit 1
        else
            error "No environment configuration found"
        fi
    fi
    
    log "Prerequisites check passed"
}

# Backup current deployment
backup_deployment() {
    log "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_NAME="backup_$(date +'%Y%m%d_%H%M%S')"
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
    
    mkdir -p "$BACKUP_PATH"
    
    # Backup volumes if they exist
    if docker volume ls | grep -q qr-studio; then
        info "Backing up Docker volumes..."
        docker run --rm -v qr-studio_redis_data:/data -v "$PWD/$BACKUP_PATH":/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
        docker run --rm -v qr-studio_backend_logs:/data -v "$PWD/$BACKUP_PATH":/backup alpine tar czf /backup/backend_logs.tar.gz -C /data .
    fi
    
    # Backup environment file
    cp "$ENV_FILE" "$BACKUP_PATH/"
    
    log "Backup created at $BACKUP_PATH"
}

# Build images
build_images() {
    log "Building Docker images..."
    
    # Set build arguments
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export VERSION=${VERSION:-"1.0.0"}
    
    info "Build arguments: BUILD_DATE=$BUILD_DATE, VCS_REF=$VCS_REF, VERSION=$VERSION"
    
    # Build images
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" build --no-cache
    else
        docker compose -f "$COMPOSE_FILE" build --no-cache
    fi
    
    log "Images built successfully"
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    # Stop existing services
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" down --remove-orphans
    else
        docker compose -f "$COMPOSE_FILE" down --remove-orphans
    fi
    
    # Start services
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" up -d
    else
        docker compose -f "$COMPOSE_FILE" up -d
    fi
    
    log "Services deployed"
}

# Health check
health_check() {
    log "Performing health checks..."
    
    # Wait for services to start
    sleep 30
    
    # Check backend health
    info "Checking backend health..."
    for i in {1..10}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log "Backend health check passed"
            break
        fi
        if [ $i -eq 10 ]; then
            error "Backend health check failed"
        fi
        info "Waiting for backend... ($i/10)"
        sleep 10
    done
    
    # Check frontend health
    info "Checking frontend health..."
    for i in {1..10}; do
        if curl -f http://localhost/health &> /dev/null; then
            log "Frontend health check passed"
            break
        fi
        if [ $i -eq 10 ]; then
            error "Frontend health check failed"
        fi
        info "Waiting for frontend... ($i/10)"
        sleep 10
    done
    
    # Check Redis
    info "Checking Redis..."
    if docker exec qr-studio-redis-prod redis-cli ping | grep -q PONG; then
        log "Redis health check passed"
    else
        error "Redis health check failed"
    fi
    
    log "All health checks passed"
}

# Show status
show_status() {
    log "Deployment status:"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" ps
    else
        docker compose -f "$COMPOSE_FILE" ps
    fi
    
    info "Services are available at:"
    info "  Frontend: http://localhost"
    info "  Backend API: http://localhost:8000"
    info "  API Documentation: http://localhost:8000/api/docs"
    info "  Health Check: http://localhost/health"
}

# Cleanup old images
cleanup() {
    log "Cleaning up old images..."
    docker image prune -f
    docker volume prune -f
    log "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting QR Studio production deployment..."
    
    check_prerequisites
    backup_deployment
    build_images
    deploy_services
    health_check
    show_status
    cleanup
    
    log "Deployment completed successfully!"
    info "Check the logs with: docker-compose -f $COMPOSE_FILE logs -f"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log "Stopping services..."
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" down
        else
            docker compose -f "$COMPOSE_FILE" down
        fi
        log "Services stopped"
        ;;
    "restart")
        log "Restarting services..."
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" restart
        else
            docker compose -f "$COMPOSE_FILE" restart
        fi
        log "Services restarted"
        ;;
    "logs")
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" logs -f
        else
            docker compose -f "$COMPOSE_FILE" logs -f
        fi
        ;;
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|status|health}"
        echo "  deploy  - Full deployment (default)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show service logs"
        echo "  status  - Show service status"
        echo "  health  - Run health checks"
        exit 1
        ;;
esac
