#!/bin/bash

# AgentForge Start Script

echo "Starting AgentForge services..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose is not installed. Please install Docker and docker-compose first."
    exit 1
fi

# Start all services
docker-compose up -d

echo ""
echo "AgentForge services started successfully!"
echo ""
echo "Services:"
echo "  - API:    http://localhost:8000"
echo "  - Web:    http://localhost:3000"
echo "  - DB:     localhost:5432"
echo "  - Redis:  localhost:6379"
echo "  - Chroma: localhost:8100"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop:      docker-compose down"
