#!/bin/bash

echo "=== Testing Loki + Grafana Logging Setup ==="
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Desktop."
    exit 1
fi

echo "✅ docker-compose found"
echo ""

# Start logging services
echo "Starting Loki and Grafana..."
cd "$(dirname "$0")"
docker-compose -f docker-compose-logging.yml up -d

echo ""
echo "Waiting for services to be ready (30 seconds)..."
sleep 30

# Check if services are running
echo ""
echo "Checking service status..."
docker-compose -f docker-compose-logging.yml ps

echo ""
echo "=== Services Ready ==="
echo ""
echo "Grafana: http://localhost:3001"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Loki API: http://localhost:3100"
echo ""
echo "To send a test log:"
echo "  curl -X POST http://localhost:3100/loki/api/v1/push \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"streams\":[{\"stream\":{\"service\":\"test\"},\"values\":[[\"$(date +%s)000000000\",\"Test log message\"]]}]}'"
echo ""
echo "To stop services: docker-compose -f logging/docker-compose-logging.yml down"
echo ""

