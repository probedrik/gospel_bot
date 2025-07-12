#!/bin/bash

# Server-side script for updating Gospel Bot
# This script should be run on the production server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE="probedrik/gospel-bot"
CONTAINER_NAME="bible-bot"
COMPOSE_FILE="docker-compose.yml"

echo -e "${BLUE}🚀 Gospel Bot Server Update Script${NC}"
echo "=================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if docker-compose.yml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "docker-compose.yml not found in current directory"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running or not accessible"
    exit 1
fi

echo -e "${BLUE}📥 Pulling latest image from Docker Hub...${NC}"
if docker pull $DOCKER_IMAGE:latest; then
    print_status "Successfully pulled latest image"
else
    print_error "Failed to pull latest image"
    exit 1
fi

echo -e "${BLUE}🛑 Stopping current bot...${NC}"
if docker-compose down; then
    print_status "Successfully stopped current containers"
else
    print_warning "No running containers to stop"
fi

# Optional: Clean up old images (uncomment if needed)
# echo -e "${BLUE}🧹 Cleaning up old images...${NC}"
# docker image prune -f

echo -e "${BLUE}🚀 Starting updated bot...${NC}"
if docker-compose up -d; then
    print_status "Successfully started updated bot"
else
    print_error "Failed to start updated bot"
    exit 1
fi

# Wait a moment for container to fully start
echo -e "${BLUE}⏳ Waiting for container to start...${NC}"
sleep 5

echo -e "${BLUE}📊 Checking container status...${NC}"
if docker-compose ps | grep -q "Up"; then
    print_status "Bot is running successfully"
    
    # Show container status
    echo -e "\n${BLUE}Container Status:${NC}"
    docker-compose ps
    
    # Show recent logs
    echo -e "\n${BLUE}Recent logs (last 20 lines):${NC}"
    docker-compose logs --tail=20 bot
    
    echo -e "\n${GREEN}✅ Update completed successfully!${NC}"
    
    # Ask if user wants to see live logs
    echo -e "\n${YELLOW}Do you want to view live logs? (y/n):${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${BLUE}📋 Showing live logs (Ctrl+C to exit):${NC}"
        docker-compose logs -f bot
    fi
else
    print_error "Bot failed to start properly"
    echo -e "\n${BLUE}Container status:${NC}"
    docker-compose ps
    echo -e "\n${BLUE}Error logs:${NC}"
    docker-compose logs bot
    exit 1
fi

# Show useful commands
echo -e "\n${BLUE}📚 Useful commands:${NC}"
echo "  View logs:           docker-compose logs -f bot"
echo "  Check status:        docker-compose ps"
echo "  Restart bot:         docker-compose restart bot"
echo "  Stop bot:            docker-compose down"
echo "  Update again:        ./update-server.sh" 