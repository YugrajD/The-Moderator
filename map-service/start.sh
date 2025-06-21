#!/bin/bash

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the map generation service
echo "Starting map generation service..."
npm start 