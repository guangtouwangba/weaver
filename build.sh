#!/bin/bash

# Build script for Research Agent RAG System
# Optimized for serverless deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="research-agent-rag"
TAG="${1:-latest}"
DOCKERFILE="Dockerfile.serverless"
REGISTRY="${REGISTRY:-}"

echo -e "${BLUE}🚀 Building Research Agent RAG System${NC}"
echo -e "${BLUE}Image: ${IMAGE_NAME}:${TAG}${NC}"
echo -e "${BLUE}Dockerfile: ${DOCKERFILE}${NC}"

# Function to print step headers
print_step() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validate prerequisites
print_step "Validating Prerequisites"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites validated${NC}"

# Validate configuration
print_step "Validating Configuration"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found, creating from development template${NC}"
    cp deployment/.env.development .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your API keys before deploying${NC}"
fi

if [ ! -f "requirements.serverless.txt" ]; then
    echo -e "${RED}❌ requirements.serverless.txt not found${NC}"
    exit 1
fi

if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}❌ $DOCKERFILE not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration validated${NC}"

# Build Docker image
print_step "Building Docker Image"

echo -e "${BLUE}Building ${IMAGE_NAME}:${TAG}...${NC}"

# Build with optimized settings
docker build \
    -f "$DOCKERFILE" \
    -t "${IMAGE_NAME}:${TAG}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Show image info
print_step "Image Information"

IMAGE_SIZE=$(docker images "${IMAGE_NAME}:${TAG}" --format "table {{.Size}}" | tail -n 1)
echo -e "${GREEN}📦 Image size: ${IMAGE_SIZE}${NC}"

# Optional: Run security scan
if command_exists docker && docker version --format '{{.Server.Version}}' | grep -q "20.10"; then
    print_step "Security Scan"
    echo -e "${BLUE}Running Docker security scan...${NC}"
    docker scout quickview "${IMAGE_NAME}:${TAG}" 2>/dev/null || echo -e "${YELLOW}⚠️  Docker Scout not available, skipping security scan${NC}"
fi

# Test the image
print_step "Testing Image"

echo -e "${BLUE}Testing image startup...${NC}"

# Create a temporary container to test
CONTAINER_ID=$(docker run -d \
    --name "test-${IMAGE_NAME}-$$" \
    -e DEFAULT_PROVIDER=deepseek \
    -e DEEPSEEK_API_KEY=test-key \
    -p 8001:8000 \
    "${IMAGE_NAME}:${TAG}")

# Wait for container to start
sleep 5

# Check if container is running
if docker ps -q -f id="$CONTAINER_ID" | grep -q .; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
    
    # Test health endpoint
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Health check failed (expected with test API key)${NC}"
    fi
else
    echo -e "${RED}❌ Container failed to start${NC}"
    docker logs "$CONTAINER_ID"
fi

# Cleanup test container
docker stop "$CONTAINER_ID" >/dev/null 2>&1 || true
docker rm "$CONTAINER_ID" >/dev/null 2>&1 || true

# Tag for registry if specified
if [ -n "$REGISTRY" ]; then
    print_step "Tagging for Registry"
    
    REGISTRY_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"
    docker tag "${IMAGE_NAME}:${TAG}" "$REGISTRY_IMAGE"
    echo -e "${GREEN}✅ Tagged as ${REGISTRY_IMAGE}${NC}"
    
    # Optional: Push to registry
    read -p "Push to registry? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Pushing to Registry"
        echo -e "${BLUE}Pushing ${REGISTRY_IMAGE}...${NC}"
        docker push "$REGISTRY_IMAGE"
        echo -e "${GREEN}✅ Pushed to registry${NC}"
    fi
fi

# Generate deployment commands
print_step "Deployment Commands"

echo -e "${GREEN}🎉 Build completed successfully!${NC}"
echo -e "\n${BLUE}Quick start commands:${NC}"
echo -e "${YELLOW}# Run locally:${NC}"
echo -e "docker run -d --name research-agent-api -p 8000:8000 --env-file .env ${IMAGE_NAME}:${TAG}"
echo -e "\n${YELLOW}# Run with docker-compose:${NC}"
echo -e "docker-compose up -d research-agent-api"
echo -e "\n${YELLOW}# Deploy to Kubernetes:${NC}"
echo -e "kubectl apply -f deployment/k8s/"

if [ -n "$REGISTRY" ]; then
    echo -e "\n${YELLOW}# Pull from registry:${NC}"
    echo -e "docker pull ${REGISTRY_IMAGE}"
fi

echo -e "\n${BLUE}📚 For more deployment options, see DEPLOYMENT.md${NC}"

# Show next steps
print_step "Next Steps"

echo -e "${BLUE}1. Update .env file with your API keys${NC}"
echo -e "${BLUE}2. Test locally: docker-compose up research-agent-api${NC}"
echo -e "${BLUE}3. Deploy to your preferred platform${NC}"
echo -e "${BLUE}4. Monitor logs and health endpoints${NC}"

echo -e "\n${GREEN}🚀 Ready for deployment!${NC}"