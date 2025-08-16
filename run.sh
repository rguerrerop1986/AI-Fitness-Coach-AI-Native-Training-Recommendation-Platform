#!/bin/bash

# Fitness Coach App - Local Development Setup

echo "🚀 Starting Fitness Coach App..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. You can modify it if needed."
fi

# Build and start the services
echo "🔨 Building and starting services..."
docker-compose up --build

echo "✅ Application is starting up!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/api/docs/"
echo ""
echo "👤 Demo Credentials:"
echo "   Coach: coach / demo123"
echo "   Assistant: assistant / demo123"
echo ""
echo "Press Ctrl+C to stop the application"
